from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import hashlib
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "super_secret_bank_key" 

# Database Helper
def get_db():
    conn = sqlite3.connect("bank.db")
    conn.row_factory = sqlite3.Row
    return conn

# Security Helper
def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

# --- ROUTES ---

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        pin = hash_pin(request.form["pin"])
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, pin, balance) VALUES (?, ?, ?)", (username, pin, 0))
            conn.commit()
            return redirect("/login")
        except sqlite3.IntegrityError:
            return "Username already exists."
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
        return "Invalid credentials."
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    
    conn = get_db()
    # Updated to fetch * so we get acc_no and pin hash
    user_data = conn.execute("SELECT * FROM users WHERE username=?", (session["user"],)).fetchone()
    
    # Fetch last 5 transactions
    txns = conn.execute("SELECT type, amount, date FROM transactions WHERE username=? ORDER BY id DESC LIMIT 5", (session["user"],)).fetchall()
    
    return render_template("dashboard.html", 
                           user=session["user"], 
                           acc_no=user_data['acc_no'],
                           pin_hash=user_data['pin'],
                           balance=user_data['balance'], 
                           transactions=txns)

@app.route("/deposit", methods=["POST"])
def deposit():
    if "user" not in session: return redirect("/login")
    
    try:
        amt = float(request.form["amount"])
        if amt > 0:
            conn = get_db()
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            conn.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amt, session["user"]))
            conn.execute("INSERT INTO transactions (username, type, amount, date) VALUES (?, ?, ?, ?)", 
                         (session["user"], "Deposit", amt, date))
            conn.commit()
    except ValueError:
        pass
    return redirect("/dashboard")

@app.route("/withdraw", methods=["POST"])
def withdraw():
    if "user" not in session: return redirect("/login")
    
    try:
        amt = float(request.form["amount"])
        conn = get_db()
        user_row = conn.execute("SELECT balance FROM users WHERE username=?", (session["user"],)).fetchone()
        bal = user_row['balance']
        
        if 0 < amt <= bal:
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            conn.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amt, session["user"]))
            conn.execute("INSERT INTO transactions (username, type, amount, date) VALUES (?, ?, ?, ?)", 
                         (session["user"], "Withdraw", amt, date))
            conn.commit()
    except (ValueError, TypeError):
        pass
    return redirect("/dashboard")

@app.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if "user" not in session: return redirect("/login")

    if request.method == "POST":
        pin_input = hash_pin(request.form["pin"])
        username = session["user"]
        conn = get_db()
        user_data = conn.execute("SELECT pin FROM users WHERE username=?", (username,)).fetchone()
        
        if user_data and user_data['pin'] == pin_input:
            conn.execute("DELETE FROM transactions WHERE username=?", (username,))
            conn.execute("DELETE FROM users WHERE username=?", (username,))
            conn.commit()
            session.clear()
            return redirect("/")
        return "Incorrect PIN. Deletion failed."
    
    return render_template("delete_confirm.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)