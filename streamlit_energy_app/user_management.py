import streamlit as st 
from require_login import require_login 
from db import get_user_collection 
from verify import hash_password 



import pandas as pd
from bson import ObjectId




def user_management_page():
    require_login()
    st.title("🛠️ User Management")
    user_coll = get_user_collection()

    # Fetch all users
    users = list(user_coll.find({}, {"password": 0}))  # hide hashes
    if not users:
        st.info("No users found in the system.")
        return

    df = pd.DataFrame(users)
    df = df.rename(columns={
        "_id": "user_id",
        "username": "Username",
        "email": "Email",
        "first_name": "First Name",
        "last_name": "Last Name",
        "role": "Role",
        "created_at": "Created At",
        "disabled": "Disabled",  # optional field
    })

    # Show in a table
    st.subheader("Existing Users")
    st.dataframe(df.set_index("user_id"), use_container_width=True)


    #Pending role requests
    st.subheader("Pending Role Requests")
    pending = list(user_coll.find({
        "approved": False,
        "requested_role": {"$in": ["manager","admin"]}
    }))
    if pending:
        for u in pending:
            col1, col2, col3 = st.columns([2,2,1])
            col1.write(f"**{u['username']}**  ({u['email']})")
            col2.write(f"wants **{u['requested_role']}** access")
            if col3.button("✅ Approve", key=f"app_{u['_id']}"):
                user_coll.update_one(
                    {"_id": u["_id"]},
                    {"$set": {
                        "role": u["requested_role"],
                        "approved": True
                    }}
                )
                st.success(f"{u['username']} is now {u['requested_role']}.")
                st.experimental_rerun()
            if col3.button("❌ Reject", key=f"rej_{u['_id']}"):
                # either leave them as resident or delete, your choice
                user_coll.update_one(
                    {"_id": u["_id"]},
                    {"$set": {
                        "requested_role": "resident",
                        "approved": True
                    }}
                )
                st.info(f"{u['username']}'s request was rejected.")
                st.experimental_rerun()
    else:
        st.write("No pending requests.")
    st.markdown("---")


    st.markdown("---")
    st.subheader("Modify a User")

    # Select a user by id
    user_ids = df["user_id"].astype(str).tolist()
    selected = st.selectbox("Pick a user to modify", user_ids)

    if selected:
        user_doc = user_coll.find_one({"_id": ObjectId(selected)})
        # display current values
        st.write(f"**Username:** {user_doc['username']}")
        st.write(f"**Email:** {user_doc['email']}")
        st.write(f"**Current Role:** {user_doc['role']}")
        disabled = user_doc.get("disabled", False)

        # Role change
        new_role = st.selectbox("New Role", ["admin", "manager", "resident"], index=["admin","manager","resident"].index(user_doc["role"]))
        if st.button("Update Role"):
            user_coll.update_one(
                {"_id": ObjectId(selected)},
                {"$set": {"role": new_role}}
            )
            st.success(f"Role updated to `{new_role}`")
            st.experimental_rerun()

        # Enable / disable login
        toggle_label = "Revoke Access" if not disabled else "Restore Access"
        if st.button(toggle_label):
            user_coll.update_one(
                {"_id": ObjectId(selected)},
                {"$set": {"disabled": not disabled}}
            )
            st.success(f"Access {'revoked' if not disabled else 'restored'}")
            st.experimental_rerun()

        # Delete user
        if st.button("❌ Delete User"):
            user_coll.delete_one({"_id": ObjectId(selected)})
            st.success("User deleted")
            st.experimental_rerun()

    st.markdown("---")
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
            st.experimental_rerun()