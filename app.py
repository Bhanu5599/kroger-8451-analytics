import streamlit as st
from google.cloud import bigquery
from utils.auth import ensure_users_table, logout
from utils.ui import apply_theme

st.set_page_config(
    page_title="Kroger / 84.51° Analytics Portal",
    page_icon="🛒",
    layout="wide"
)

ensure_users_table()

def home_page():
    apply_theme(
        "Kroger / 84.51° Analytics Portal",
        "Assignment-aligned Kroger / 84.51° insights on household behavior, basket combinations, and churn risk."
    )

    client = bigquery.Client(project="final-group-project-10")

    query = """
    SELECT
      COUNT(DISTINCT hshd_num) AS total_households,
      COUNT(DISTINCT basket_num) AS total_baskets,
      CAST(SUM(spend) AS FLOAT64) AS total_sales
    FROM `final-group-project-10.retail_analytics.v_retail_joined`
    """
    df = client.query(query).to_dataframe()

    top_left, top_right = st.columns([5, 1])
    with top_left:
        st.markdown(
            f"""
            <div class="soft-card">
                <h3 style="margin-top:0;">Welcome, {st.session_state.get('username','user')}</h3>
                <p class="mini-note">Signed in as {st.session_state.get('email','')}</p>
                <p class="mini-note">Use the navigation menu to access the required assignment modules.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_right:
        st.button("Sign out", on_click=logout, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Households", int(df.loc[0, "total_households"]))
    c2.metric("Total Baskets", int(df.loc[0, "total_baskets"]))
    c3.metric("Total Sales", f"${df.loc[0, 'total_sales']:,.2f}")

    st.markdown(
        """
        <div class="soft-card" style="margin-top:16px;">
            <h4 style="margin-top:0;">Assignment coverage</h4>
            <p class="mini-note"><strong>Profile:</strong> account details and sign out</p>
            <p class="mini-note"><strong>Household Data Pull:</strong> searchable household-level output</p>
            <p class="mini-note"><strong>Latest Data Upload:</strong> upload refreshed raw files</p>
            <p class="mini-note"><strong>Kroger / 84.51° Dashboard:</strong> engagement, demographics, and preferences</p>
            <p class="mini-note"><strong>Basket Analysis & Churn Prediction:</strong> Questions 7 and 8</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.session_state.get("authenticated", False):
    pg = st.navigation(
        {
            "Navigation": [
                st.Page(home_page, title="Home", icon="🏠", default=True),
                st.Page("pages/1_Account.py", title="Profile", icon="👤"),
                st.Page("pages/2_Household_Search.py", title="Household Data Pull", icon="🔎"),
                st.Page("pages/3_Data_Upload.py", title="Latest Data Upload", icon="⬆️"),
                st.Page("pages/4_Dashboard.py", title="Kroger / 84.51° Dashboard", icon="📊"),
                st.Page("pages/5_Basket_and_Churn.py", title="Basket Analysis & Churn Prediction", icon="🧠"),
            ]
        }
    )
else:
    pg = st.navigation(
        [
            st.Page("login_page.py", title="Sign In", icon="🔐", default=True),
        ]
    )

pg.run()
