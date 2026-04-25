import streamlit as st
from utils.auth import register_user, login_user
from utils.ui import apply_theme

apply_theme(
    "Sign In to Kroger / 84.51° Analytics",
    "Create an account or sign in",
    hide_sidebar=True
)

st.markdown('<div class="auth-wrap">', unsafe_allow_html=True)
left, right = st.columns([1.1, 1])

with left:
    st.markdown(
        """
        <div class="soft-card">
            <h3 style="margin-top:0;">Project access</h3>
            <p class="mini-note">This portal supports the assignment workflow: sign in, household search, latest data upload, dashboard analysis, basket analysis, and churn prediction for Kroger / 84.51° retail insights.</p>
            <p class="mini-note">Create an account once, then use the remaining pages after authentication.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    tab1, tab2 = st.tabs(["Sign In", "Create Account"])

    with tab1:
        with st.form("login_form", clear_on_submit=False):
            st.subheader("Welcome back")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            login_btn = st.form_submit_button("Sign In", use_container_width=True)

        if login_btn:
            ok, msg = login_user(username, password)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    with tab2:
        with st.form("register_form", clear_on_submit=True):
            st.subheader("Create your account")
            new_username = st.text_input("Username", placeholder="Choose a username")
            new_email = st.text_input("Email", placeholder="Enter your email")
            new_password = st.text_input("Password", type="password", placeholder="Create a password")
            register_btn = st.form_submit_button("Register", use_container_width=True)

        if register_btn:
            ok, msg = register_user(new_username, new_email, new_password)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

st.markdown("</div>", unsafe_allow_html=True)
