import os
import json
import streamlit as st

def _credentials_path():
    return os.path.join(os.path.dirname(__file__), "credentials.json")

def load_credentials():
    path = _credentials_path()
    if not os.path.exists(path):
        return {"users": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def authenticate(username: str, password: str) -> bool:
    creds = load_credentials()
    for u in creds.get("users", []):
        if u.get("username") == username and u.get("password") == password:
            return True
    return False

def login() -> bool:
    # Already authenticated
    if st.session_state.get("user"):
        return True

    st.title("STAGE Inventory — Sign in")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        if authenticate(username.strip(), password):
            st.session_state["user"] = username.strip()
            st.rerun()
        else:
            st.error("Invalid username or password.")
    return False

def logout():
    if "user" in st.session_state:
        del st.session_state["user"]
    st.rerun()