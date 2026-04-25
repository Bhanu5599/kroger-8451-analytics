import streamlit as st
from utils.auth import require_login, logout
from utils.ui import apply_theme

require_login()
apply_theme("Account Details", "View your profile information and manage your session.")

left, right = st.columns([3, 1])

with left:
    st.markdown(
        f"""
        <div class="soft-card">
            <h3 style="margin-top:0;">Profile</h3>
            <p class="mini-note"><strong>Username:</strong> {st.session_state.get('username', '')}</p>
            <p class="mini-note"><strong>Email:</strong> {st.session_state.get('email', '')}</p>
            <p class="mini-note"><strong>Status:</strong> Signed in</p>
            <p class="mini-note">Use the other pages to search households, upload data, review the dashboard, and analyze basket/churn insights.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="soft-card" style="margin-top:16px;">
            <h4 style="margin-top:0;">What you can do next</h4>
            <p class="mini-note">• Household Search: run the required household-level data pull</p>
            <p class="mini-note">• Data Upload: upload refreshed CSV files</p>
            <p class="mini-note">• Dashboard: review business-friendly analytics</p>
            <p class="mini-note">• Basket and Churn: answer Questions 7 and 8</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        """
        <div class="soft-card">
            <h4 style="margin-top:0;">Session</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.button("Sign out", on_click=logout, use_container_width=True)
