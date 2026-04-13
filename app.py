from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "banking_secret_key_123"

def get_db():
    conn = sqlite3.connect("bank.db")
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
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
        pin = hash_pin(request.form["pin"])
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, pin, balance) VALUES (?, ?, ?)", (username, pin, 0))
            conn.commit()
            return redirect("/login")
        except:
            return "User already exists"
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
        return "Invalid credentials"
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect("/login")
    conn = get_db()
    balance = conn.execute("SELECT balance FROM users WHERE username=?", (session["user"],)).fetchone()[0]
    # Fetch last 5 transactions
    txns = conn.execute("SELECT type, amount, date FROM transactions WHERE username=? ORDER BY id DESC LIMIT 5", (session["user"],)).fetchall()
    return render_template("dashboard.html", user=session["user"], balance=balance, transactions=txns)

@app.route("/deposit", methods=["POST"])
def deposit():
    amt = float(request.form["amount"])
    if amt > 0:
        conn = get_db()
        conn.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amt, session["user"]))
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn.execute("INSERT INTO transactions (username, type, amount, date) VALUES (?, ?, ?, ?)", 
                     (session["user"], "Deposit", amt, date))
        conn.commit()
    return redirect("/dashboard")

@app.route("/withdraw", methods=["POST"])
def withdraw():
    amt = float(request.form["amount"])
    conn = get_db()
    bal = conn.execute("SELECT balance FROM users WHERE username=?", (session["user"],)).fetchone()[0]
    if 0 < amt <= bal:
        conn.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amt, session["user"]))
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn.execute("INSERT INTO transactions (username, type, amount, date) VALUES (?, ?, ?, ?)", 
                     (session["user"], "Withdraw", amt, date))
        conn.commit()
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)