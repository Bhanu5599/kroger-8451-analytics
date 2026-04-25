import streamlit as st

def apply_theme(title: str, subtitle: str = "", hide_sidebar: bool = False):
    sidebar_css = """
    section[data-testid="stSidebar"] {display:none;}
    """ if hide_sidebar else ""

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(180deg, #f7f9fc 0%, #eef3fb 100%);
        }}
        .block-container {{
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1180px;
        }}
        .hero {{
            background: linear-gradient(135deg, #0f172a, #1d4ed8);
            border-radius: 22px;
            padding: 28px 30px;
            color: white;
            box-shadow: 0 20px 40px rgba(15, 23, 42, 0.18);
            margin-bottom: 18px;
        }}
        .hero h1 {{
            margin: 0;
            font-size: 2.1rem;
            font-weight: 800;
        }}
        .hero p {{
            margin: 8px 0 0 0;
            color: #dbeafe;
            font-size: 1rem;
        }}
        .soft-card {{
            background: white;
            border-radius: 18px;
            padding: 18px 18px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 10px 24px rgba(2, 6, 23, 0.06);
        }}
        .mini-note {{
            font-size: 0.92rem;
            color: #475569;
        }}
        div[data-testid="stMetric"] {{
            background: white;
            border: 1px solid #e5e7eb;
            padding: 14px;
            border-radius: 16px;
            box-shadow: 0 10px 24px rgba(2, 6, 23, 0.05);
        }}
        .auth-wrap {{
            max-width: 900px;
            margin: 0 auto;
        }}
        {sidebar_css}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
