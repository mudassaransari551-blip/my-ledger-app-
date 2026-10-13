import sqlite3
import streamlit as st

# System Limits (Risk Management)
MAX_SINGLE_ADD_LIMIT = 20000.0  # Ek dafa me max entry limit
MAX_USER_BALANCE_CAP = 50000.0  # User ka max balance limit

st.set_page_config(page_title="Ledger Management", layout="centered")

conn = sqlite3.connect("ledger.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    balance REAL DEFAULT 0.0
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    type TEXT,
    amount REAL,
    note TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""
)
conn.commit()

st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["User Login", "Admin Panel"])

if menu == "User Login":
    st.header("👤 User Balance Dashboard")

    user_input = st.text_input("Username")
    pass_input = st.text_input("Password", type="password")

    if st.button("Check Balance"):
        cursor.execute(
            "SELECT balance FROM users WHERE username=? AND password=?",
            (user_input, pass_input),
        )
        result = cursor.fetchone()

        if result:
            st.success(f"Welcome, {user_input}!")
            st.metric(label="Current Balance", value=f"PKR {result[0]:,.2f}")

            st.info("⚠️ Note: Maximum payout limit per user is PKR 50,000.")

            st.subheader("Transaction History")
            cursor.execute(
                "SELECT type, amount, note, timestamp FROM history WHERE username=? ORDER BY id DESC",
                (user_input,),
            )
            logs = cursor.fetchall()
            if logs:
                for log in logs:
                    st.text(
                        f"[{log[3]}] {log[0].upper()}: PKR {log[1]} ({log[2]})"
                    )
            else:
                st.info("No transaction history available.")
        else:
            st.error("Invalid Username or Password")

elif menu == "Admin Panel":
    st.header("🔑 Admin Control Panel")

    admin_pass = st.text_input("Enter Admin Secret Key", type="password")

    if admin_pass == "admin123":
        st.success("Admin Authenticated")

        tab1, tab2, tab3 = st.tabs(
            ["Create New User", "Add/Deduct Points", "All Users List"]
        )

        with tab1:
            st.subheader("Add New User")
            new_user = st.text_input("New Username")
            new_pass = st.text_input("Set User Password")
            initial_bal = st.number_input(
                "Initial Balance", value=0.0, max_value=MAX_USER_BALANCE_CAP
            )

            if st.button("Create Account"):
                if new_user and new_pass:
                    try:
                        cursor.execute(
                            "INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
                            (new_user, new_pass, initial_bal),
                        )
                        conn.commit()
                        st.success(f"Account for {new_user} created!")
                    except:
                        st.error("Username pehle se maujood hai!")
                else:
                    st.warning("Tamam fields fill karein.")

        with tab2:
            st.subheader("Update Balance (With Safety Limits)")
            cursor.execute("SELECT username, balance FROM users")
            users_data = cursor.fetchall()

            if users_data:
                users_dict = {row[0]: row[1] for row in users_data}
                selected_user = st.selectbox(
                    "Select User", list(users_dict.keys())
                )

                st.write(
                    f"Current Balance: PKR {users_dict[selected_user]:,.2f}"
                )

                action = st.selectbox(
                    "Action",
                    ["Add Money (Win/Deposit)", "Deduct Money (Loss/Withdraw)"],
                )
                amount = st.number_input(
                    "Amount (PKR)",
                    min_value=1.0,
                    max_value=MAX_SINGLE_ADD_LIMIT,
                )
                note = st.text_input(
                    "Note / Description", value="Manual Adjustment"
                )

                if st.button("Submit Transaction"):
                    current_bal = users_dict[selected_user]

                    if action == "Add Money (Win/Deposit)":
                        new_bal = current_bal + amount
                        if new_bal > MAX_USER_BALANCE_CAP:
                            st.error(
                                f"Transaction Blocked! Balance limit exceeds PKR {MAX_USER_BALANCE_CAP}."
                            )
                        else:
                            cursor.execute(
                                "UPDATE users SET balance = balance + ? WHERE username = ?",
                                (amount, selected_user),
                            )
                            cursor.execute(
                                "INSERT INTO history (username, type, amount, note) VALUES (?, ?, ?, ?)",
                                (selected_user, "Credit", amount, note),
                            )
                            conn.commit()
                            st.success(
                                f"PKR {amount} added to {selected_user}'s account!"
                            )
                    else:
                        cursor.execute(
                            "UPDATE users SET balance = balance - ? WHERE username = ?",
                            (amount, selected_user),
                        )
                        cursor.execute(
                            "INSERT INTO history (username, type, amount, note) VALUES (?, ?, ?, ?)",
                            (selected_user, "Debit", amount, note),
                        )
                        conn.commit()
                        st.success(
                            f"PKR {amount} deducted from {selected_user}'s account!"
                        )
            else:
                st.info("Pehle koi account banayein.")

        with tab3:
            st.subheader("All Accounts Ledger")
            cursor.execute("SELECT username, balance FROM users")
            all_users = cursor.fetchall()
            if all_users:
                st.table(all_users)
            else:
                st.info("Koi records maujood nahi hain.")
    elif admin_pass != "":
        st.error("Ghalt Admin Password!")
