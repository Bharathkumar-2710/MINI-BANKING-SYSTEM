from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    return sqlite3.connect("bank.db")

def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

@app.route("/")
def home():
    return render_template("index.html")

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        pin = hash_pin(request.form["pin"])

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, pin, balance) VALUES (?, ?, ?)",
                (username, pin, 0)
            )
            conn.commit()
            return redirect("/login")
        except:
            return "User already exists"

    return render_template("register.html")

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        pin = hash_pin(request.form["pin"])

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND pin=?",
            (username, pin)
        )

        if cursor.fetchone():
            session["user"] = username
            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("login.html")

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (session["user"],))
    balance = cursor.fetchone()[0]

    return render_template("dashboard.html", user=session["user"], balance=balance)

# DEPOSIT
@app.route("/deposit", methods=["POST"])
def deposit():
    amt = float(request.form["amount"])
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE username=?",
        (amt, session["user"])
    )
    conn.commit()

    return redirect("/dashboard")

# WITHDRAW
@app.route("/withdraw", methods=["POST"])
def withdraw():
    amt = float(request.form["amount"])
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE username=?", (session["user"],))
    bal = cursor.fetchone()[0]

    if amt <= bal:
        cursor.execute(
            "UPDATE users SET balance = balance - ? WHERE username=?",
            (amt, session["user"])
        )
        conn.commit()

    return redirect("/dashboard")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)