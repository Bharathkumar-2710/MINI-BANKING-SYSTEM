from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import hashlib
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "super_secret_bank_key" 

def get_db():
    conn = sqlite3.connect("bank.db")
    conn.row_factory = sqlite3.Row
    return conn

def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        pin_raw = request.form["pin"]
        if len(pin_raw) < 4:
            flash("PIN must be at least 4 digits.")
            return redirect("/register")
        
        pin = hash_pin(pin_raw)
        try:
            conn = get_db()
            conn.execute("INSERT INTO users (username, pin, balance) VALUES (?, ?, ?)", (username, pin, 0))
            conn.commit()
            flash("Registration successful!")
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash("Username already exists.")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        pin = hash_pin(request.form["pin"])
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND pin=?", (username, pin)).fetchone()
        if user:
            session["user"] = username
            return redirect("/dashboard")
        flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect("/login")
    conn = get_db()
    user_data = conn.execute("SELECT * FROM users WHERE username=?", (session["user"],)).fetchone()
    txns = conn.execute("SELECT type, amount, date FROM transactions WHERE username=? ORDER BY id DESC LIMIT 5", (session["user"],)).fetchall()
    return render_template("dashboard.html", user=session["user"], acc_no=user_data['acc_no'], pin_hash=user_data['pin'], balance=user_data['balance'], transactions=txns)

@app.route("/deposit", methods=["POST"])
def deposit():
    if "user" not in session: return redirect("/login")
    try:
        amt = float(request.form["amount"])
        if amt > 0:
            conn = get_db()
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            conn.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amt, session["user"]))
            conn.execute("INSERT INTO transactions (username, type, amount, date) VALUES (?, ?, ?, ?)", (session["user"], "Deposit", amt, date))
            conn.commit()
    except ValueError: flash("Invalid amount.")
    return redirect("/dashboard")

@app.route("/withdraw", methods=["POST"])
def withdraw():
    if "user" not in session: return redirect("/login")
    try:
        amt = float(request.form["amount"])
        conn = get_db()
        user_row = conn.execute("SELECT balance FROM users WHERE username=?", (session["user"],)).fetchone()
        if 0 < amt <= user_row['balance']:
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            conn.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amt, session["user"]))
            conn.execute("INSERT INTO transactions (username, type, amount, date) VALUES (?, ?, ?, ?)", (session["user"], "Withdraw", amt, date))
            conn.commit()
        else: flash("Insufficient funds.")
    except: flash("Error processing withdrawal.")
    return redirect("/dashboard")

@app.route("/transfer", methods=["POST"])
def transfer():
    if "user" not in session: return redirect("/login")
    try:
        target_acc = request.form["target_acc"]
        amt = float(request.form["amount"])
        conn = get_db()
        sender = conn.execute("SELECT acc_no, balance FROM users WHERE username=?", (session["user"],)).fetchone()
        receiver = conn.execute("SELECT username FROM users WHERE acc_no=?", (target_acc,)).fetchone()

        if receiver and sender['balance'] >= amt and amt > 0:
            if int(target_acc) == sender['acc_no']:
                flash("Cannot transfer to yourself.")
            else:
                date = datetime.now().strftime("%Y-%m-%d %H:%M")
                conn.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amt, session["user"]))
                conn.execute("UPDATE users SET balance = balance + ? WHERE acc_no=?", (amt, target_acc))
                conn.execute("INSERT INTO transactions (username, type, amount, date) VALUES (?, ?, ?, ?)", (session["user"], f"Sent to {receiver['username']}", amt, date))
                conn.execute("INSERT INTO transactions (username, type, amount, date) VALUES (?, ?, ?, ?)", (receiver['username'], f"Received from {session['user']}", amt, date))
                conn.commit()
                flash("Transfer successful!")
        else: flash("Transfer failed. Check account number or balance.")
    except: flash("Invalid transfer details.")
    return redirect("/dashboard")

@app.route("/change_pin", methods=["GET", "POST"])
def change_pin():
    if "user" not in session: return redirect("/login")
    if request.method == "POST":
        old_pin = hash_pin(request.form["old_pin"])
        new_pin = request.form["new_pin"]
        conn = get_db()
        user = conn.execute("SELECT pin FROM users WHERE username=?", (session["user"],)).fetchone()
        if user['pin'] == old_pin and len(new_pin) >= 4:
            conn.execute("UPDATE users SET pin=? WHERE username=?", (hash_pin(new_pin), session["user"]))
            conn.commit()
            flash("PIN changed successfully!")
            return redirect("/dashboard")
        flash("Incorrect current PIN or new PIN too short.")
    return render_template("change_pin.html")

@app.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if "user" not in session: return redirect("/login")
    if request.method == "POST":
        pin_input = hash_pin(request.form["pin"])
        conn = get_db()
        user_data = conn.execute("SELECT pin FROM users WHERE username=?", (session["user"],)).fetchone()
        if user_data['pin'] == pin_input:
            conn.execute("DELETE FROM transactions WHERE username=?", (session["user"],))
            conn.execute("DELETE FROM users WHERE username=?", (session["user"],))
            conn.commit()
            session.clear()
            return redirect("/")
        flash("Incorrect PIN.")
    return render_template("delete_confirm.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)