import streamlit as st 
from require_login import require_login
from db import get_user_collection, get_messages_collection
from email_utils import send_email 
import pandas as pd 





def communications_page():
    require_login()
    user = st.session_state.user
    role = user["role"]
    if role not in ("admin","manager"):
        st.error("🚫 You don’t have permission to view this page.")
        return

    st.title("💬 Communications")
    users_coll    = get_user_collection()
    messages_coll = get_messages_collection()

    # Build list of possible recipients (only admins/managers except yourself)
    candidates = users_coll.find(
        {"role": {"$in": ["admin","manager"]}, "username": {"$ne": user["username"]}}
    )
    options = []
    for u in candidates:
        label = f"{u['first_name']} {u['last_name']} ({u['role']})"
        options.append((label, u["username"], u["email"]))

    st.subheader("Send a Message")
    with st.form("msg_form", clear_on_submit=True):
        choice = st.selectbox(
            "Send to…", [lbl for lbl,_,_ in options], format_func=lambda x: x
        )
        content = st.text_area("Your message")
        send    = st.form_submit_button("📨 Send")

    if send and content.strip():
        # look up username & email for the chosen label
        recipient = next(r for r in options if r[0] == choice)
        rec_label, rec_username, rec_email = recipient

        # insert into Mongo
        messages_coll.insert_one({
            "sender": user["username"],
            "recipient": rec_username,
            "content": content.strip(),
            "timestamp": pd.Timestamp.now(),
            "read": False,
        })
        st.success(f"Message sent to {rec_label}!")

        # email notification
        subject = f"[EMADS] New message from {user['username']}"
        body    = (
            f"Hello {rec_label},\n\n"
            f"You have a new message in the EMADS portal from {user['username']}.\n"
            f"Please log in to view it.\n\n"
            "— EMADS System"
        )
        try:
            send_email(rec_email, subject, body)
            st.info(f"📧 Notification sent to {rec_label}’s email.")
        except Exception as e:
            st.error(f"Failed to send email: {e}")

    st.markdown("---")

    # … rest of your inbox logic, now filtering on `recipient` instead of `recipient_role` …
    st.subheader("Inbox")
    inbox = list(messages_coll.find({"recipient": user["username"]})
                 .sort("timestamp", -1))
    if not inbox:
        st.info("No messages.")
        return

    for msg in inbox:
        raw_ts = msg["timestamp"]
        if hasattr(raw_ts, "to_pydatetime"):
            dt = raw_ts.to_pydatetime()
        else:
            dt = raw_ts
            ts = dt.strftime("%Y-%m-%d %H:%M")

        new_flag = not msg.get("read", False)
        header = f"**From:** {msg['sender']}   **At:** {ts}"
        if new_flag:
            header += "   :new:"
        st.markdown(header)
        st.write(msg["content"])
        if new_flag and st.button("Mark read 📖", key=str(msg["_id"])):
            messages_coll.update_one(
                {"_id": msg["_id"]}, {"$set": {"read": True}}
            )
            st.experimental_rerun()
        st.markdown("---")
