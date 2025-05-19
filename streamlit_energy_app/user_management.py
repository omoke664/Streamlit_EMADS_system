import streamlit as st 
from require_login import require_login 
from db import get_user_collection 
from verify import hash_password 
import pandas as pd

def user_management_page():
    require_login()
    st.title("🛠️ User Management")
    user_coll = get_user_collection()

    # … your Existing Users and Pending Requests blocks …

    st.markdown("---")
    st.subheader("Modify a User")

    # 1) Fetch all users (exclude password hashes)
    users = list(user_coll.find({}, {"password": 0}))

    if not users:
        st.info("No users to modify.")
        return

    # 2) Build DataFrame, ensure disabled column exists
    df = pd.DataFrame(users)
    if "disabled" not in df.columns:
        df["disabled"] = False

    # 3) Rename columns and set index to username
    df = (
        df[["username", "email", "first_name", "last_name", "role", "disabled"]]
        .rename(columns={
            "username": "Username",
            "email": "Email",
            "first_name": "First Name",
            "last_name": "Last Name",
            "role": "Role",
            "disabled": "Disabled",
        })
        .set_index("Username")
    )

    st.dataframe(df, use_container_width=True)

    # 4) Let admin pick a username
    selected_username = st.selectbox("Pick a user to modify", df.index.tolist())

    if selected_username:
        user_doc = user_coll.find_one({"username": selected_username})
        st.write(f"**Email:** {user_doc['email']}")
        st.write(f"**Current Role:** {user_doc['role']}")
        disabled = user_doc.get("disabled", False)

        # Role change
        new_role = st.selectbox(
            "New Role", ["admin", "manager", "resident"],
            index=["admin", "manager", "resident"].index(user_doc["role"])
        )
        if st.button("Update Role"):
            user_coll.update_one(
                {"username": selected_username},
                {"$set": {"role": new_role}}
            )
            st.success(f"Role updated to `{new_role}`")
            return

        # Enable / disable login
        toggle_label = "Revoke Access" if not disabled else "Restore Access"
        if st.button(toggle_label):
            user_coll.update_one(
                {"username": selected_username},
                {"$set": {"disabled": not disabled}}
            )
            st.success(f"Access {'revoked' if not disabled else 'restored'}")
            return

        # Delete user
        if st.button("❌ Delete User"):
            user_coll.delete_one({"username": selected_username})
            st.success("User deleted")
            return

    # … your “Add a New User” form …
        st.subheader("Add a New User")
        with st.form("add_user_form", clear_on_submit=True):
            un = st.text_input("Username")
            em = st.text_input("Email")
            fn = st.text_input("First Name")
            ln = st.text_input("Last Name")
            pw = st.text_input("Password", type="password")
            rl = st.selectbox("Role", ["admin", "manager", "resident"])
            submitted = st.form_submit_button("Create User")

        if submitted:
            if user_coll.find_one({"username": un}) or user_coll.find_one({"email": em}):
                st.error("Username or email already in use.")
            else:
                user_coll.insert_one({
                    "username": un,
                    "email": em,
                    "first_name": fn,
                    "last_name": ln,
                    "password": hash_password(pw),
                    "role": rl,
                    "created_at": pd.Timestamp.now(),
                    "disabled": False
                })
                st.success("New user added!")
                return
