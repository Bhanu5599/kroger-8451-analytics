import os
import re
import bcrypt
import streamlit as st
from google.cloud import bigquery

PROJECT_ID = os.getenv("PROJECT_ID", "final-group-project-10")
TABLE = f"`{PROJECT_ID}.retail_analytics.app_users`"

def get_client():
    return bigquery.Client(project=PROJECT_ID)

def ensure_users_table():
    query = f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        username STRING NOT NULL,
        email STRING NOT NULL,
        password_hash STRING NOT NULL,
        created_at TIMESTAMP NOT NULL
    )
    """
    get_client().query(query).result()

def _query_df(query, params=None):
    job_config = bigquery.QueryJobConfig(query_parameters=params or [])
    return get_client().query(query, job_config=job_config).to_dataframe()

def valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()))

def register_user(username: str, email: str, password: str):
    username = username.strip().lower()
    email = email.strip().lower()

    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not valid_email(email):
        return False, "Enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    existing = _query_df(
        f"SELECT username, email FROM {TABLE} WHERE username = @username OR email = @email LIMIT 1",
        [
            bigquery.ScalarQueryParameter("username", "STRING", username),
            bigquery.ScalarQueryParameter("email", "STRING", email),
        ],
    )
    if not existing.empty:
        return False, "That username or email already exists."

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    insert_query = f"""
    INSERT INTO {TABLE} (username, email, password_hash, created_at)
    VALUES (@username, @email, @password_hash, CURRENT_TIMESTAMP())
    """
    get_client().query(
        insert_query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("username", "STRING", username),
                bigquery.ScalarQueryParameter("email", "STRING", email),
                bigquery.ScalarQueryParameter("password_hash", "STRING", password_hash),
            ]
        ),
    ).result()

    return True, "Account created successfully. Please sign in."

def login_user(username: str, password: str):
    username = username.strip().lower()

    df = _query_df(
        f"SELECT username, email, password_hash FROM {TABLE} WHERE username = @username LIMIT 1",
        [bigquery.ScalarQueryParameter("username", "STRING", username)],
    )

    if df.empty:
        return False, "User not found."

    stored_hash = df.iloc[0]["password_hash"]
    if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        st.session_state["authenticated"] = True
        st.session_state["username"] = df.iloc[0]["username"]
        st.session_state["email"] = df.iloc[0]["email"]
        return True, "Signed in successfully."

    return False, "Incorrect password."

def logout():
    for key in ["authenticated", "username", "email"]:
        if key in st.session_state:
            del st.session_state[key]

def require_login():
    if not st.session_state.get("authenticated", False):
        st.warning("Please sign in from the Home page first.")
        st.stop()
