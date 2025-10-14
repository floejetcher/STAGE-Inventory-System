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

def authenticate(username: str, password: str):
    creds = load_credentials()
    for u in creds.get("users", []):
        if u.get("username") == username and u.get("password") == password:
            return {"username": u.get("username"), "role": u.get("role", "guest")}
    return None

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
        user = authenticate(username.strip(), password)
        if user:
            st.session_state["user"] = user["username"]
            st.session_state["role"] = user.get("role", "guest")
            st.rerun()
        else:
            st.error("Invalid username or password.")
    return False

def logout():
    for k in ("user", "role"):
        st.session_state.pop(k, None)
    # Do not call st.rerun() here; trigger it from normal code after the button press.

def current_user() -> str | None:
    return st.session_state.get("user")

def current_role() -> str:
    return st.session_state.get("role", "guest")

def is_admin() -> bool:
    return current_role() == "admin"