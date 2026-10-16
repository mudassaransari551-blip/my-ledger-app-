elif menu == "Admin Panel":
    st.header("🔑 Admin Control Panel")

    admin_pass = st.text_input("Enter Admin Secret Key", type="password")
    admin_login_btn = st.button("Admin Login")

    if admin_login_btn or admin_pass == "admin123":
        if admin_pass == "admin123":
            st.session_state["admin_logged_in"] = True
        else:
            st.error("Ghalt Admin Password!")

    if st.session_state.get("admin_logged_in", False):
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
