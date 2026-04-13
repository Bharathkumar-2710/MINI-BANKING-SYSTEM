import sqlite3
import hashlib
from datetime import datetime

DB = "bank.db"

# ---------------- DB ----------------
def get_db():
    return sqlite3.connect(DB)

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        acc_no INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        pin TEXT,
        balance REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        type TEXT,
        amount REAL,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

# ---------------- AUTH ----------------
def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

def create_user(username, pin):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, pin, balance) VALUES (?, ?, ?)",
            (username, hash_pin(pin), 0)
        )
        conn.commit()
        return "Success"
    except:
        return "User exists"
    finally:
        conn.close()

def validate_user(username, pin):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND pin=?",
        (username, hash_pin(pin))
    )

    user = cursor.fetchone()
    conn.close()

    return user is not None

# ---------------- UTILS ----------------
def add_transaction(cursor, user, t_type, amount):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO transactions (username, type, amount, date) VALUES (?, ?, ?, ?)",
        (user, t_type, amount, date)
    )

def get_balance(user):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE username=?", (user,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return 0

    return result[0]

# ---------------- CORE ----------------
def deposit(user, amt):
    if amt <= 0:
        return "Invalid amount"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE username=?",
        (amt, user)
    )

    add_transaction(cursor, user, "Deposit", amt)

    conn.commit()
    conn.close()

    return "Deposited"


def withdraw(user, amt):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE username=?", (user,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return "User not found"

    bal = result[0]

    if amt <= 0:
        conn.close()
        return "Invalid amount"

    if amt > bal:
        conn.close()
        return "Insufficient balance"

    cursor.execute(
        "UPDATE users SET balance = balance - ? WHERE username=?",
        (amt, user)
    )

    add_transaction(cursor, user, "Withdraw", -amt)

    conn.commit()
    conn.close()

    return "Withdrawn"


def transfer(user, receiver_acc, amt):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT acc_no, balance FROM users WHERE username=?",
        (user,)
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return "User not found"

    sender_acc, bal = result

    if amt <= 0 or amt > bal:
        conn.close()
        return "Invalid balance"

    cursor.execute("SELECT username FROM users WHERE acc_no=?", (receiver_acc,))
    rec = cursor.fetchone()

    if not rec:
        conn.close()
        return "Receiver not found"

    receiver = rec[0]

    try:
        conn.execute("BEGIN")

        cursor.execute(
            "UPDATE users SET balance = balance - ? WHERE acc_no=?",
            (amt, sender_acc)
        )

        cursor.execute(
            "UPDATE users SET balance = balance + ? WHERE acc_no=?",
            (amt, receiver_acc)
        )

        add_transaction(cursor, user, f"Sent to {receiver}", -amt)
        add_transaction(cursor, receiver, f"Received from {user}", amt)

        conn.commit()
        return "Success"

    except:
        conn.rollback()
        return "Transfer failed"

    finally:
        conn.close()

# ---------------- TRANSACTIONS ----------------
def get_transactions(user):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT type, amount, date
        FROM transactions
        WHERE username=?
        ORDER BY id DESC
    """, (user,))

    data = cursor.fetchall()
    conn.close()

    return data


def get_mini(user):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT type, amount, date
        FROM transactions
        WHERE username=?
        ORDER BY id DESC LIMIT 5
    """, (user,))

    data = cursor.fetchall()
    conn.close()

    return data


def delete_account(user, pin):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT pin FROM users WHERE username=?", (user,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return "User not found"

    if result[0] != hash_pin(pin):
        conn.close()
        return "Wrong PIN"

    cursor.execute("DELETE FROM transactions WHERE username=?", (user,))
    cursor.execute("DELETE FROM users WHERE username=?", (user,))

    conn.commit()
    conn.close()

    return "Deleted"