import sqlite3
import streamlit as st

# System Limits (Risk Management)
MAX_SINGLE_ADD_LIMIT = 20000.0  # Ek dafa me max limit
MAX_USER_BALANCE_CAP = 50000.0  # User ka max balance limit

st.set_page_config(page_title="Sports Ledger & Betting", layout="centered")

conn = sqlite3.connect("ledger.db", check_same_thread=False)
cursor = conn.cursor()

# Database Tables Initialization
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

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    amount REAL,
    trx_id TEXT,
    status TEXT DEFAULT 'Pending'
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    match_name TEXT,
    prediction TEXT,
    stake REAL,
    status TEXT DEFAULT 'Pending'
)
"""
)
conn.commit()

st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["User Portal", "Admin Panel"])

if menu == "User Portal":
    st.header("👤 User Dashboard & Betting Slip")

    user_input = st.text_input("Username")
    pass_input = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute(
            "SELECT balance FROM users WHERE username=? AND password=?",
            (user_input, pass_input),
        )
        result = cursor.fetchone()

        if result:
            st.session_state["logged_user"] = user_input
            st.success(f"Welcome back, {user_input}!")
        else:
            st.error("Invalid Username or Password")

    if "logged_user" in st.session_state:
        current_user = st.session_state["logged_user"]

        # Fetch latest balance
        cursor.execute(
            "SELECT balance FROM users WHERE username=?", (current_user,)
        )
        bal_res = cursor.fetchone()
        current_bal = bal_res[0] if bal_res else 0.0

        st.metric(label="Your Available Balance", value=f"PKR {current_bal:,.2f}")
        st.info(
            f"⚠️ Limits: Max Balance Cap is PKR {MAX_USER_BALANCE_CAP:,.0f}"
        )

        tab_u1, tab_u2, tab_u3, tab_u4 = st.tabs(
            ["Deposit Request", "Place Bet", "My Bets", "History"]
        )

        with tab_u1:
            st.subheader("Request Balance Deposit")
            st.write(
                "Pehle Admin ko JazzCash/Easypaisa transfer karein, phir yahan request dalein."
            )
            dep_amount = st.number_input(
                "Deposit Amount (PKR)",
                min_value=1.0,
                max_value=MAX_SINGLE_ADD_LIMIT,
                key="dep_amt",
            )
            trx_id = st.text_input("Transaction ID / Reference No")

            if st.button("Submit Deposit Request"):
                if trx_id:
                    cursor.execute(
                        "INSERT INTO deposits (username, amount, trx_id, status) VALUES (?, ?, ?, 'Pending')",
                        (current_user, dep_amount, trx_id),
                    )
                    conn.commit()
                    st.success(
                        "Deposit request submitted! Admin approval ka intezar karein."
                    )
                else:
                    st.warning("Please enter Transaction ID.")

        with tab_u2:
            st.subheader("Place Sports Bet")
            match_name = st.text_input(
                "Match Name (e.g., Pakistan vs India)"
            )
            prediction = st.text_input(
                "Your Pick / Prediction (e.g., Pakistan Win)"
            )
            stake_amount = st.number_input(
                "Bet Amount (PKR)", min_value=1.0, key="stake_amt"
            )

            if st.button("Place Bet"):
                if stake_amount > current_bal:
                    st.error("Aapke paas itna balance nahi hai!")
                elif stake_amount > MAX_SINGLE_ADD_LIMIT:
                    st.error(
                        f"Max single bet limit is PKR {MAX_SINGLE_ADD_LIMIT}"
                    )
                else:
                    # Deduct amount temporarily or lock it
                    cursor.execute(
                        "UPDATE users SET balance = balance - ? WHERE username = ?",
                        (stake_amount, current_user),
                    )
                    cursor.execute(
                        "INSERT INTO bets (username, match_name, prediction, stake, status) VALUES (?, ?, ?, ?, 'Active')",
                        (
                            current_user,
                            match_name,
                            prediction,
                            stake_amount,
                        ),
                    )
                    conn.commit()
                    st.success("Bet successfully placed!")
                    st.rerun()

        with tab_u3:
            st.subheader("Your Active & Past Bets")
            cursor.execute(
                "SELECT match_name, prediction, stake, status FROM bets WHERE username=?",
                (current_user,),
            )
            user_bets = cursor.fetchall()
            if user_bets:
                for b in user_bets:
                    st.text(
                        f"Match: {b[0]} | Pick: {b[1]} | Stake: PKR {b[2]} | Status: {b[3]}"
                    )
            else:
                st.info("No bets found.")

        with tab_u4:
            st.subheader("Transaction History")
            cursor.execute(
                "SELECT type, amount, note, timestamp FROM history WHERE username=? ORDER BY id DESC",
                (current_user,),
            )
            logs = cursor.fetchall()
            if logs:
                for log in logs:
                    st.text(
                        f"[{log[3]}] {log[0].upper()}: PKR {log[1]} ({log[2]})"
                    )
            else:
                st.info("No history available.")

elif menu == "Admin Panel":
    st.header("🔑 Admin Control Panel")

    admin_pass = st.text_input("Enter Admin Secret Key", type="password")

    if admin_pass == "admin123":
        st.success("Admin Authenticated Successfully")

        tab_a1, tab_a2, tab_a3, tab_a4, tab_a5 = st.tabs(
            [
                "Create User",
                "Approve Deposits",
                "Manage Bets & Payouts",
                "Manual Adjust",
                "All Users",
            ]
        )

        with tab_a1:
            st.subheader("Add New User Account")
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

        with tab_a2:
            st.subheader("Pending Deposit Requests")
            cursor.execute(
                "SELECT id, username, amount, trx_id FROM deposits WHERE status='Pending'"
            )
            pending_deps = cursor.fetchall()

            if pending_deps:
                for d in pending_deps:
                    st.write(
                        f"ID: {d[0]} | User: **{d[1]}** | Amount: **PKR {d[2]}** | TrxID: {d[3]}"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Approve Deposit {d[0]}"):
                            # Check balance cap
                            cursor.execute(
                                "SELECT balance FROM users WHERE username=?",
                                (d[1],),
                            )
                            c_bal = cursor.fetchone()[0]
                            if c_bal + d[2] > MAX_USER_BALANCE_CAP:
                                st.error(
                                    "Exceeds Max User Balance Cap! Approved blocked."
                                )
                            else:
                                cursor.execute(
                                    "UPDATE users SET balance = balance + ? WHERE username = ?",
                                    (d[2], d[1]),
                                )
                                cursor.execute(
                                    "UPDATE deposits SET status='Approved' WHERE id=?",
                                    (d[0],),
                                )
                                cursor.execute(
                                    "INSERT INTO history (username, type, amount, note) VALUES (?, 'Credit', ?, 'Deposit Approved')",
                                    (d[1], d[2]),
                                )
                                conn.commit()
                                st.success(f"Approved PKR {d[2]} for {d[1]}!")
                                st.rerun()
                    with col2:
                        if st.button(f"Reject Deposit {d[0]}"):
                            cursor.execute(
                                "UPDATE deposits SET status='Rejected' WHERE id=?",
                                (d[0],),
                            )
                            conn.commit()
                            st.warning("Deposit rejected.")
                            st.rerun()
            else:
                st.info("No pending deposit requests.")

        with tab_a3:
            st.subheader("Manage Active Bets & Declare Winners")
            cursor.execute(
                "SELECT id, username, match_name, prediction, stake FROM bets WHERE status='Active'"
            )
            active_bets = cursor.fetchall()

            if active_bets:
                for b in active_bets:
                    st.write(
                        f"Bet ID: {b[0]} | User: **{b[1]}** | Match: {b[2]} | Pick: {b[3]} | Stake: PKR {b[4]}"
                    )
                    win_amount = st.number_input(
                        f"Payout Amount for Bet {b[0]} (PKR)",
                        min_value=0.0,
                        max_value=MAX_SINGLE_ADD_LIMIT,
                        key=f"payout_{b[0]}",
                    )

                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button(f"Mark Win & Pay {b[0]}"):
                            cursor.execute(
                                "UPDATE users SET balance = balance + ? WHERE username = ?",
                                (win_amount, b[1]),
                            )
                            cursor.execute(
                                "UPDATE bets SET status='Won' WHERE id=?",
                                (b[0],),
                            )
                            cursor.execute(
                                "INSERT INTO history (username, type, amount, note) VALUES (?, 'Credit', ?, 'Bet Won Payout')",
                                (b[1], win_amount),
                            )
                            conn.commit()
                            st.success(
                                f"Paid PKR {win_amount} to {b[1]} for winning bet!"
                            )
                            st.rerun()
                    with col_b2:
                        if st.button(f"Mark Lost {b[0]}"):
                            cursor.execute(
                                "UPDATE bets SET status='Lost' WHERE id=?",
                                (b[0],),
                            )
                            conn.commit()
                            st.info(f"Bet {b[0]} marked as Lost.")
                            st.rerun()
            else:
                st.info("No active bets to settle.")

        with tab_a4:
            st.subheader("Manual Balance Adjustment")
            cursor.execute("SELECT username, balance FROM users")
            u_data = cursor.fetchall()
            if u_data:
                u_dict = {row[0]: row[1] for row in u_data}
                sel_u = st.selectbox("Select User", list(u_dict.keys()))
                act = st.selectbox("Action", ["Add Balance", "Deduct Balance"])
                amt = st.number_input(
                    "Amount (PKR)",
                    min_value=1.0,
                    max_value=MAX_SINGLE_ADD_LIMIT,
                )
                nt = st.text_input("Reason", value="Admin Adjustment")

                if st.button("Execute Adjustment"):
                    if act == "Add Balance":
                        if u_dict[sel_u] + amt > MAX_USER_BALANCE_CAP:
                            st.error("Exceeds max balance cap!")
                        else:
                            cursor.execute(
                                "UPDATE users SET balance = balance + ? WHERE username = ?",
                                (amt, sel_u),
                            )
                            cursor.execute(
                                "INSERT INTO history (username, type, amount, note) VALUES (?, 'Credit', ?, ?)",
                                (sel_u, amt, nt),
                            )
                            conn.commit()
                            st.success(
                                f"Added PKR {amt} to {sel_u}'s account."
                            )
                    else:
                        cursor.execute(
                            "UPDATE users SET balance = balance - ? WHERE username = ?",
                            (amt, sel_u),
                        )
                        cursor.execute(
                            "INSERT INTO history (username, type, amount, note) VALUES (?, 'Debit', ?, ?)",
                            (sel_u, amt, nt),
                        )
                        conn.commit()
                        st.success(
                            f"Deducted PKR {amt} from {sel_u}'s account."
                        )

        with tab_a5:
            st.subheader("All User Accounts")
            cursor.execute("SELECT username, balance FROM users")
            all_u = cursor.fetchall()
            if all_u:
                st.table(all_u)
            else:
                st.info("No users found.")
    elif admin_pass != "":
        st.error("Ghalt Admin Password!")
