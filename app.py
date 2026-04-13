from flask import Flask, render_template, request, redirect, session
import bank

app = Flask(__name__)
app.secret_key = "secret123"

# Initialize DB
bank.init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        pin = request.form["pin"]

        msg = bank.create_user(username, pin)

        if msg == "Success":
            return redirect("/login")
        else:
            return msg

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        pin = request.form["pin"]

        if bank.validate_user(username, pin):
            session["user"] = username
            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    balance = bank.get_balance(session["user"])
    return render_template("dashboard.html", user=session["user"], balance=balance)

# ---------------- DEPOSIT ----------------
@app.route("/deposit", methods=["POST"])
def deposit():
    if "user" not in session:
        return redirect("/login")

    amt = float(request.form["amount"])

    msg = bank.deposit(session["user"], amt)
    return redirect("/dashboard")

# ---------------- WITHDRAW ----------------
@app.route("/withdraw", methods=["POST"])
def withdraw():
    if "user" not in session:
        return redirect("/login")

    amt = float(request.form["amount"])

    msg = bank.withdraw(session["user"], amt)
    return redirect("/dashboard")

# ---------------- TRANSFER ----------------
@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        acc = int(request.form["account"])
        amt = float(request.form["amount"])

        msg = bank.transfer(session["user"], acc, amt)

        if msg != "Success":
            return msg

        return redirect("/dashboard")

    return render_template("transfer.html")

# ---------------- TRANSACTIONS ----------------
@app.route("/transactions")
def transactions():
    if "user" not in session:
        return redirect("/login")

    data = bank.get_transactions(session["user"])
    return render_template("transactions.html", data=data)

# ---------------- MINI STATEMENT ----------------
@app.route("/mini")
def mini():
    if "user" not in session:
        return redirect("/login")

    data = bank.get_mini(session["user"])
    return render_template("mini.html", data=data)

# ---------------- DELETE ACCOUNT ----------------
@app.route("/delete", methods=["GET", "POST"])
def delete():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        pin = request.form["pin"]

        msg = bank.delete_account(session["user"], pin)

        if msg == "Deleted":
            session.clear()
            return redirect("/")

        return msg

    return render_template("delete.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)