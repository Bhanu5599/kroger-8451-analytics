import os
import streamlit as st
from google.cloud import bigquery
from utils.auth import require_login
from utils.ui import apply_theme

PROJECT_ID = os.getenv("PROJECT_ID", "final-group-project-10")

require_login()
apply_theme("Kroger / 84.51° Dashboard", "Business-friendly views for engagement, demographics, and shopping preferences.")

client = bigquery.Client(project=PROJECT_ID)

overview_tab, demo_tab, pref_tab = st.tabs(["Business Overview", "Demographic Insights", "Shopping Preferences"])

with overview_tab:
    query_kpi = f"""
    SELECT
      COUNT(DISTINCT hshd_num) AS total_households,
      CAST(SUM(spend) AS FLOAT64) AS total_sales,
      CAST(AVG(spend) AS FLOAT64) AS average_spend,
      CAST(SUM(units) AS INT64) AS total_units
    FROM `{PROJECT_ID}.retail_analytics.v_retail_joined`
    """
    df_kpi = client.query(query_kpi).to_dataframe()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Households", int(df_kpi.loc[0, "total_households"]))
    c2.metric("Total Sales", f"${df_kpi.loc[0, 'total_sales']:,.2f}")
    c3.metric("Average Spend per Transaction", f"${df_kpi.loc[0, 'average_spend']:,.2f}")
    c4.metric("Total Units Sold", int(df_kpi.loc[0, "total_units"]))

    query_trend = f"""
    SELECT
      purchase_date AS purchase_date,
      CAST(SUM(spend) AS FLOAT64) AS total_sales
    FROM `{PROJECT_ID}.retail_analytics.v_retail_joined`
    GROUP BY purchase_date
    ORDER BY purchase_date
    """
    df_trend = client.query(query_trend).to_dataframe()
    st.subheader("Customer Spending Over Time")
    st.caption("This view shows how customer spending changes across the transaction period.")
    st.line_chart(df_trend.set_index("purchase_date"))

    query_dept = f"""
    SELECT
      department AS department_name,
      CAST(SUM(spend) AS FLOAT64) AS total_sales
    FROM `{PROJECT_ID}.retail_analytics.v_retail_joined`
    GROUP BY department_name
    ORDER BY total_sales DESC
    LIMIT 10
    """
    df_dept = client.query(query_dept).to_dataframe()
    st.subheader("Top Departments by Sales")
    st.bar_chart(df_dept.set_index("department_name"))

with demo_tab:
    query_hh = f"""
    SELECT
      hshd_size AS household_size,
      CAST(AVG(spend) AS FLOAT64) AS average_spend
    FROM `{PROJECT_ID}.retail_analytics.v_retail_joined`
    WHERE hshd_size IS NOT NULL
    GROUP BY household_size
    ORDER BY household_size
    """
    df_hh = client.query(query_hh).to_dataframe()
    st.subheader("Average Spend by Household Size")
    st.bar_chart(df_hh.set_index("household_size"))

    query_income = f"""
    SELECT
      income_range AS income_bracket,
      CAST(SUM(spend) AS FLOAT64) AS total_sales
    FROM `{PROJECT_ID}.retail_analytics.v_retail_joined`
    WHERE income_range IS NOT NULL
    GROUP BY income_bracket
    ORDER BY total_sales DESC
    """
    df_income = client.query(query_income).to_dataframe()
    df_income.columns = ["Income Bracket", "Total Sales"]
    st.subheader("Sales by Income Bracket")
    st.dataframe(df_income, use_container_width=True)

    query_loyalty = f"""
    SELECT
      CASE
        WHEN LOWER(CAST(loyalty_flag AS STRING)) IN ('y', 'yes', 'true', '1') THEN 'Loyalty Member'
        ELSE 'Not a Loyalty Member'
      END AS loyalty_status,
      CAST(SUM(spend) AS FLOAT64) AS total_sales
    FROM `{PROJECT_ID}.retail_analytics.v_retail_joined`
    GROUP BY loyalty_status
    ORDER BY total_sales DESC
    """
    df_loyalty = client.query(query_loyalty).to_dataframe()
    st.subheader("Sales by Loyalty Membership")
    st.bar_chart(df_loyalty.set_index("loyalty_status"))

with pref_tab:
    query_brand = f"""
    SELECT
      CASE
        WHEN brand_type IS NULL OR TRIM(CAST(brand_type AS STRING)) = '' THEN 'Unknown Brand Type'
        ELSE CAST(brand_type AS STRING)
      END AS brand_preference,
      CAST(SUM(spend) AS FLOAT64) AS total_sales
    FROM `{PROJECT_ID}.retail_analytics.v_retail_joined`
    GROUP BY brand_preference
    ORDER BY total_sales DESC
    """
    df_brand = client.query(query_brand).to_dataframe()
    st.subheader("Private vs National Brand Preference")
    st.bar_chart(df_brand.set_index("brand_preference"))

    query_org = f"""
    SELECT
      CASE
        WHEN LOWER(CAST(natural_organic_flag AS STRING)) IN ('true', '1', 'y', 'yes') THEN 'Organic'
        ELSE 'Not Organic / Unknown'
      END AS product_type,
      CAST(SUM(spend) AS FLOAT64) AS total_sales
    FROM `{PROJECT_ID}.retail_analytics.v_retail_joined`
    GROUP BY product_type
    ORDER BY total_sales DESC
    """
    df_org = client.query(query_org).to_dataframe()
    st.subheader("Organic vs Non-Organic Products")
    st.bar_chart(df_org.set_index("product_type"))
