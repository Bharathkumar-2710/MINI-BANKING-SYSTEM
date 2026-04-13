from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = "secret123"

# DB connection
def get_db():
    return sqlite3.connect("bank.db")

# Hash PIN
def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

# Home Page
@app.route("/")
def home():
    return render_template("index.html")

# Register
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

# Login
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

        user = cursor.fetchone()

        if user:
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT balance FROM users WHERE username=?",
        (session["user"],)
    )

    balance = cursor.fetchone()[0]

    return render_template("dashboard.html", user=session["user"], balance=balance)

# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)