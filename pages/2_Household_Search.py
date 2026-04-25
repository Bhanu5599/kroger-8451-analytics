import os
import streamlit as st
from google.cloud import bigquery
from utils.auth import require_login
from utils.ui import apply_theme

PROJECT_ID = os.getenv("PROJECT_ID", "final-group-project-10")

require_login()
apply_theme("Household Data Pull", "Search any household and return the linked sample pull.")

client = bigquery.Client(project=PROJECT_ID)

left, right = st.columns([1, 2])

with left:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    hshd_num = st.number_input("Enter Household Number", min_value=1, step=1, value=10)
    search = st.button("Run Data Pull", use_container_width=True)
    st.markdown(
        "<p class='mini-note'>Results are sorted by household, basket, date, product, department, and commodity.</p>",
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

if search:
    query = f"""
    SELECT
      hshd_num,
      basket_num,
      purchase_date,
      product_num,
      department,
      commodity,
      spend,
      units,
      store_region,
      week_num,
      year,
      loyalty_flag,
      age_range,
      marital_status,
      income_range,
      homeowner_desc,
      hshd_composition,
      hshd_size,
      children
    FROM `{PROJECT_ID}.retail_analytics.v_retail_joined`
    WHERE hshd_num = @hshd_num
    ORDER BY hshd_num, basket_num, purchase_date, product_num, department, commodity
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("hshd_num", "INT64", int(hshd_num))
        ]
    )

    df = client.query(query, job_config=job_config).to_dataframe()

    with right:
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Rows", len(df))
            c2.metric("Distinct Baskets", int(df["basket_num"].nunique()))
            c3.metric("Total Spend", f"${df['spend'].astype(float).sum():,.2f}")

            display_df = df.rename(columns={
                "hshd_num": "Household Number",
                "basket_num": "Basket Number",
                "purchase_date": "Purchase Date",
                "product_num": "Product Number",
                "department": "Department",
                "commodity": "Commodity",
                "spend": "Spend",
                "units": "Units",
                "store_region": "Store Region",
                "week_num": "Week Number",
                "year": "Year",
                "loyalty_flag": "Loyalty Flag",
                "age_range": "Age Range",
                "marital_status": "Marital Status",
                "income_range": "Income Range",
                "homeowner_desc": "Homeowner Description",
                "hshd_composition": "Household Composition",
                "hshd_size": "Household Size",
                "children": "Children"
            })

            st.dataframe(display_df, use_container_width=True, height=520)
            csv = display_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Results as CSV",
                csv,
                file_name=f"hshd_{int(hshd_num)}_data_pull.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.warning("No records found for that household.")
