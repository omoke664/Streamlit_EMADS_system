import streamlit as st 
from require_login import require_login 
from db import get_user_collection, get_communications_collection
from verify import hash_password 
import pandas as pd
from datetime import datetime

def handle_role_request(username, requested_role, action):
    """Handle role request approval or rejection"""
    users = get_user_collection()
    communications = get_communications_collection()
    
    if action == "approve":
        # Update user's role and status
        users.update_one(
            {"username": username},
            {
                "$set": {
                    "role": requested_role,
                    "status": "active",
                    "requested_role": None
                }
            }
        )
        
        # Send approval notification to user
        approval_message = {
            "username": username,
            "title": "Role Request Approved",
            "message": f"""
            Your request to become a {requested_role} has been approved!

            You can now access all features available to {requested_role}s.
            Please log out and log back in to see the changes.

            Best regards,
            The EMADS Team
            """,
            "type": "system_message",
            "timestamp": datetime.now(),
            "read": False
        }
        communications.insert_one(approval_message)
        
        return True, f"Successfully approved {username}'s request to become a {requested_role}"
        
    elif action == "reject":
        # Update user's status and clear requested role
        users.update_one(
            {"username": username},
            {
                "$set": {
                    "status": "active",
                    "requested_role": None
                }
            }
        )
        
        # Send rejection notification to user
        rejection_message = {
            "username": username,
            "title": "Role Request Rejected",
            "message": f"""
            Your request to become a {requested_role} has been rejected.

            You will continue with your current role as a resident.
            If you have any questions, please contact an administrator.

            Best regards,
            The EMADS Team
            """,
            "type": "system_message",
            "timestamp": datetime.now(),
            "read": False
        }
        communications.insert_one(rejection_message)
        
        return True, f"Successfully rejected {username}'s request to become a {requested_role}"
    
    return False, "Invalid action"

def user_management_page():
    require_login()
    st.title("User Management")
    user_coll = get_user_collection()

    # Get user from session
    user = st.session_state.get('user')
    if not user or user["role"] not in ["admin", "manager"]:
        st.error("You must be an admin or manager to access this page.")
        return

    # Display Pending Role Requests
    st.subheader("Pending Role Requests")
    pending_users = list(user_coll.find({
        "requested_role": {"$in": ["admin", "manager"]},
        "status": "pending"
    }))

    if pending_users:
        for pending_user in pending_users:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**User:** {pending_user['first_name']} {pending_user['last_name']} ({pending_user['username']})")
                    st.markdown(f"**Requested Role:** {pending_user['requested_role']}")
                    st.markdown(f"**Email:** {pending_user['email']}")
                    st.caption(f"Requested on: {pending_user['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                with col2:
                    if st.button("Approve", key=f"approve_{pending_user['username']}"):
                        success, message = handle_role_request(
                            pending_user['username'],
                            pending_user['requested_role'],
                            "approve"
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    if st.button("Reject", key=f"reject_{pending_user['username']}"):
                        success, message = handle_role_request(
                            pending_user['username'],
                            pending_user['requested_role'],
                            "reject"
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                st.divider()
    else:
        st.info("No pending role requests.")

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
        if st.button("Delete User"):
            user_coll.delete_one({"username": selected_username})
            st.success("User deleted")
            return

    # Add a New User form
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
