import sqlite3
import hashlib
from datetime import datetime

# DB Connection
conn = sqlite3.connect("bank.db")
cursor = conn.cursor()

# Create Tables
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

# Hash PIN
def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

# Create Account
def create_account():
    try:
        username = input("Enter username: ")
        pin_input = input("Set PIN: ")
        pin = hash_pin(pin_input)

        cursor.execute(
            "INSERT INTO users (username, pin, balance) VALUES (?, ?, ?)",
            (username, pin, 0)
        )
        conn.commit()

        cursor.execute("SELECT acc_no FROM users WHERE username=?", (username,))
        acc_no = cursor.fetchone()[0]

        print(f"Account created successfully. Account No: {acc_no}")

    except sqlite3.IntegrityError:
        print("Username already exists.")
    except Exception as e:
        print("Error:", e)

# Login
def login():
    try:
        username = input("Username: ")
        pin_input = input("Enter PIN: ")
        pin = hash_pin(pin_input)

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND pin=?",
            (username, pin)
        )

        if cursor.fetchone():
            print("Login successful.")
            return username
        else:
            print("Invalid credentials.")
            return None

    except Exception as e:
        print("Login error:", e)
        return None

# Add Transaction
def add_transaction(user, t_type, amount):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO transactions (username, type, amount, date) VALUES (?, ?, ?, ?)",
        (user, t_type, amount, date)
    )

# Change PIN
def change_pin(user):
    try:
        print("\n🔐 Change PIN")

        old_pin_input = input("Enter current PIN: ")
        old_pin = hash_pin(old_pin_input)

        cursor.execute("SELECT pin FROM users WHERE username=?", (user,))
        real_pin = cursor.fetchone()[0]

        if old_pin != real_pin:
            print("Wrong current PIN.")
            return

        new_pin = input("Enter new PIN: ")
        confirm_pin = input("Confirm new PIN: ")

        if new_pin != confirm_pin:
            print("PINs do not match.")
            return

        if len(new_pin) < 4:
            print("PIN must be at least 4 digits.")
            return

        new_hashed = hash_pin(new_pin)

        cursor.execute("UPDATE users SET pin=? WHERE username=?", (new_hashed, user))
        conn.commit()

        print("PIN changed successfully.")

    except Exception as e:
        print("Error changing PIN:", e)

# Delete Account
def delete_account(user):
    try:
        print("\n⚠️ Delete Account")
        confirm = input("Are you sure? (yes/no): ").lower()

        if confirm != "yes":
            print("Cancelled.")
            return False

        pin_input = input("Enter your PIN: ")
        pin = hash_pin(pin_input)

        cursor.execute("SELECT pin FROM users WHERE username=?", (user,))
        real_pin = cursor.fetchone()[0]

        if pin != real_pin:
            print("Wrong PIN.")
            return False

        cursor.execute("DELETE FROM transactions WHERE username=?", (user,))
        cursor.execute("DELETE FROM users WHERE username=?", (user,))
        conn.commit()

        print("Account deleted successfully.")
        return True

    except Exception as e:
        print("Error:", e)
        return False

# Banking Menu
def banking(user):
    while True:
        print(f"\n--- Welcome {user} ---")
        print("1. Deposit")
        print("2. Withdraw")
        print("3. Balance")
        print("4. Full Transactions")
        print("5. Transfer")
        print("6. Mini Statement")
        print("7. Change PIN")
        print("8. Delete Account")
        print("9. Logout")

        choice = input("Choice: ")

        if choice == "1":
            try:
                amt = float(input("Amount: "))
                if amt <= 0:
                    print("Invalid amount.")
                    continue

                cursor.execute(
                    "UPDATE users SET balance = balance + ? WHERE username=?",
                    (amt, user)
                )
                add_transaction(user, "Deposit", amt)
                conn.commit()
                print("Amount deposited.")

            except:
                print("Invalid input.")

        elif choice == "2":
            try:
                amt = float(input("Amount: "))
                cursor.execute("SELECT balance FROM users WHERE username=?", (user,))
                bal = cursor.fetchone()[0]

                if amt <= 0:
                    print("Invalid amount.")
                elif amt <= bal:
                    cursor.execute(
                        "UPDATE users SET balance = balance - ? WHERE username=?",
                        (amt, user)
                    )
                    add_transaction(user, "Withdraw", amt)
                    conn.commit()
                    print("Amount withdrawn.")
                else:
                    print("Insufficient balance.")

            except:
                print("Invalid input.")

        elif choice == "3":
            cursor.execute("SELECT balance FROM users WHERE username=?", (user,))
            print("Balance:", cursor.fetchone()[0])

        elif choice == "4":
            cursor.execute(
                "SELECT type, amount, date FROM transactions WHERE username=?",
                (user,)
            )
            for row in cursor.fetchall():
                print(row)

        elif choice == "5":
            try:
                acc = int(input("Receiver Account No: "))
                amt = float(input("Amount: "))

                cursor.execute(
                    "SELECT acc_no, balance FROM users WHERE username=?",
                    (user,)
                )
                sender_acc, bal = cursor.fetchone()

                if acc == sender_acc:
                    print("Cannot transfer to yourself.")
                    continue

                cursor.execute("SELECT username FROM users WHERE acc_no=?", (acc,))
                rec = cursor.fetchone()

                if not rec:
                    print("Receiver not found.")
                    continue

                if amt <= 0 or amt > bal:
                    print("Invalid or insufficient balance.")
                    continue

                receiver = rec[0]

                conn.execute("BEGIN")

                cursor.execute(
                    "UPDATE users SET balance = balance - ? WHERE acc_no=?",
                    (amt, sender_acc)
                )
                cursor.execute(
                    "UPDATE users SET balance = balance + ? WHERE acc_no=?",
                    (amt, acc)
                )

                txn_id = f"TXN{int(datetime.now().timestamp())}"

                add_transaction(user, f"{txn_id} Sent to {receiver}", amt)
                add_transaction(receiver, f"{txn_id} Received from {user}", amt)

                conn.commit()
                print(f"Transfer successful. ID: {txn_id}")

            except Exception as e:
                conn.rollback()
                print("Transfer failed.", e)

        elif choice == "6":
            cursor.execute("""
            SELECT type, amount, date
            FROM transactions
            WHERE username=?
            ORDER BY id DESC LIMIT 5
            """, (user,))
            print("\n--- Last 5 Transactions ---")
            for row in cursor.fetchall():
                print(row)

        elif choice == "7":
            change_pin(user)

        elif choice == "8":
            deleted = delete_account(user)
            if deleted:
                break

        elif choice == "9":
            print("Logged out.")
            break

        else:
            print("Invalid choice.")

# Main
while True:
    print("\n=== BANK SYSTEM ===")
    print("1. Create Account")
    print("2. Login")
    print("3. Exit")

    ch = input("Choice: ")

    if ch == "1":
        create_account()
    elif ch == "2":
        user = login()
        if user:
            banking(user)
    elif ch == "3":
        print("Goodbye.")
        break
    else:
        print("Invalid choice.")

conn.close()