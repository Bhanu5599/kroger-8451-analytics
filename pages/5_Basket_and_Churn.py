import os
import streamlit as st
import pandas as pd
from google.cloud import bigquery
from utils.auth import require_login
from utils.ui import apply_theme

PROJECT_ID = os.getenv("PROJECT_ID", "final-group-project-10")
VIEW_NAME = f"`{PROJECT_ID}.retail_analytics.v_retail_joined`"

require_login()
apply_theme(
    "Basket Analysis and Churn Prediction",
    "Directly aligned to the assignment questions on product combinations, cross-selling, and disengagement risk."
)

client = bigquery.Client(project=PROJECT_ID)

@st.cache_data(ttl=600)
def run_query(query: str) -> pd.DataFrame:
    return client.query(query).to_dataframe()

basket_tab, churn_tab = st.tabs([
    "Question 7: Basket Analysis",
    "Question 8: Churn Prediction"
])

with basket_tab:
    st.markdown(
        """
        <div class="soft-card">
            <h4 style="margin-top:0;">Selected model for Basket Analysis</h4>
            <p class="mini-note"><strong>Model choice:</strong> Gradient Boosting</p>
            <p class="mini-note"><strong>Reason:</strong> Basket behavior is rarely linear. Gradient Boosting is more suitable than simple linear regression because it can capture nonlinear interactions between purchase patterns, basket size, spending, loyalty, and household behavior.</p>
            <p class="mini-note">This section includes both common product combinations and a model-based cross-sell prediction view.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    basket_query = f"""
    WITH basket_items AS (
      SELECT DISTINCT
        hshd_num,
        basket_num,
        purchase_date,
        commodity
      FROM {VIEW_NAME}
      WHERE commodity IS NOT NULL
        AND commodity != ''
    ),
    pairs AS (
      SELECT
        a.commodity AS commodity_1,
        b.commodity AS commodity_2,
        COUNT(*) AS baskets_bought_together
      FROM basket_items a
      JOIN basket_items b
        ON a.hshd_num = b.hshd_num
       AND a.basket_num = b.basket_num
       AND a.purchase_date = b.purchase_date
       AND a.commodity < b.commodity
      GROUP BY 1, 2
    ),
    totals AS (
      SELECT
        COUNT(
          DISTINCT CONCAT(
            CAST(hshd_num AS STRING), '-',
            CAST(basket_num AS STRING), '-',
            CAST(purchase_date AS STRING)
          )
        ) AS total_baskets
      FROM basket_items
    )
    SELECT
      commodity_1,
      commodity_2,
      baskets_bought_together,
      ROUND(SAFE_DIVIDE(baskets_bought_together, total_baskets) * 100, 2) AS support_percentage
    FROM pairs, totals
    ORDER BY baskets_bought_together DESC
    LIMIT 12
    """

    df_basket = run_query(basket_query)

    if not df_basket.empty:
        df_basket["Product Combination"] = df_basket["commodity_1"] + " + " + df_basket["commodity_2"]
        df_basket["Cross-Sell Action"] = (
            "Promote " + df_basket["commodity_2"] + " when " + df_basket["commodity_1"] + " appears in the basket"
        )

        display_basket = df_basket[[
            "Product Combination",
            "baskets_bought_together",
            "support_percentage",
            "Cross-Sell Action"
        ]].rename(columns={
            "baskets_bought_together": "Times Bought Together",
            "support_percentage": "Support (%)"
        })

        st.subheader("Most Common Product Combinations")
        st.dataframe(display_basket, use_container_width=True)

        st.subheader("Top Basket Combinations")
        chart_df = display_basket[["Product Combination", "Times Bought Together"]]
        st.bar_chart(chart_df.set_index("Product Combination"))

        top_pair = display_basket.iloc[0]
        st.success(
            f"Best cross-selling opportunity: {top_pair['Product Combination']} "
            f"appears together {int(top_pair['Times Bought Together'])} times."
        )
    else:
        st.warning("No basket combination data returned.")

    st.subheader("Gradient Boosting Basket Model")
    st.caption(
        "This model predicts whether a basket has strong cross-sell potential based on spend, units, "
        "basket complexity, loyalty, and household attributes."
    )

    eval_query = f"""
    SELECT *
    FROM ML.EVALUATE(MODEL `{PROJECT_ID}.retail_analytics.basket_gb_model`)
    """
    try:
        df_eval = run_query(eval_query)
        if not df_eval.empty:
            st.dataframe(df_eval, use_container_width=True)
    except Exception as e:
        st.error("basket_gb_model was not found. Create the BigQuery ML model first.")
        st.code(str(e))
        st.stop()

    predict_query = f"""
    SELECT
      hshd_num,
      basket_num,
      purchase_date,
      predicted_cross_sell_flag,
      predicted_cross_sell_flag_probs
    FROM ML.PREDICT(
      MODEL `{PROJECT_ID}.retail_analytics.basket_gb_model`,
      (
        SELECT
          hshd_num,
          basket_num,
          purchase_date,
          basket_spend,
          basket_units,
          unique_products,
          unique_commodities,
          loyalty_member,
          household_size,
          children,
          income_range,
          store_region
        FROM `{PROJECT_ID}.retail_analytics.basket_features`
      )
    )
    ORDER BY predicted_cross_sell_flag DESC
    LIMIT 20
    """

    df_pred = run_query(predict_query)

    if not df_pred.empty:
        def extract_probability(prob_list):
            try:
                for item in prob_list:
                    if str(item.get("label")) == "1":
                        return round(float(item.get("prob", 0.0)) * 100, 2)
            except Exception:
                return None
            return None

        df_pred["Cross-Sell Probability (%)"] = df_pred["predicted_cross_sell_flag_probs"].apply(extract_probability)
        display_pred = df_pred.rename(columns={
            "hshd_num": "Household Number",
            "basket_num": "Basket Number",
            "purchase_date": "Purchase Date",
            "predicted_cross_sell_flag": "Predicted Cross-Sell Flag"
        })[[
            "Household Number",
            "Basket Number",
            "Purchase Date",
            "Predicted Cross-Sell Flag",
            "Cross-Sell Probability (%)"
        ]]

        st.subheader("Model-Predicted High Cross-Sell Baskets")
        st.dataframe(display_pred, use_container_width=True)

with churn_tab:
    st.markdown(
        """
        <div class="soft-card">
            <h4 style="margin-top:0;">Churn prediction logic</h4>
            <p class="mini-note">This section supports the churn question using recent purchase activity, recency, and spending decline. Households with long inactivity or major recent spend drops are flagged as higher risk. This is supported with tables and charts.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    churn_query = f"""
    WITH maxd AS (
      SELECT MAX(purchase_date) AS max_date
      FROM {VIEW_NAME}
    ),
    hh AS (
      SELECT
        v.hshd_num,
        MAX(v.loyalty_flag) AS loyalty_flag,
        DATE_DIFF(m.max_date, MAX(v.purchase_date), DAY) AS days_since_last_purchase,
        CAST(SUM(CASE
          WHEN v.purchase_date >= DATE_SUB(m.max_date, INTERVAL 90 DAY) THEN v.spend
          ELSE 0 END) AS FLOAT64) AS spend_last_90_days,
        CAST(SUM(CASE
          WHEN v.purchase_date < DATE_SUB(m.max_date, INTERVAL 90 DAY)
           AND v.purchase_date >= DATE_SUB(m.max_date, INTERVAL 180 DAY) THEN v.spend
          ELSE 0 END) AS FLOAT64) AS spend_previous_90_days,
        COUNT(DISTINCT CASE
          WHEN v.purchase_date >= DATE_SUB(m.max_date, INTERVAL 90 DAY)
          THEN CONCAT(CAST(v.basket_num AS STRING), '-', CAST(v.purchase_date AS STRING))
          ELSE NULL END) AS baskets_last_90_days
      FROM {VIEW_NAME} v
      CROSS JOIN maxd m
      GROUP BY v.hshd_num, m.max_date
    )
    SELECT
      hshd_num,
      loyalty_flag,
      days_since_last_purchase,
      spend_last_90_days,
      spend_previous_90_days,
      baskets_last_90_days,
      CASE
        WHEN days_since_last_purchase > 90
          OR (spend_previous_90_days > 0 AND spend_last_90_days < spend_previous_90_days * 0.50) THEN 'High Risk'
        WHEN days_since_last_purchase > 60
          OR (spend_previous_90_days > 0 AND spend_last_90_days < spend_previous_90_days * 0.80) THEN 'Medium Risk'
        ELSE 'Low Risk'
      END AS churn_risk
    FROM hh
    ORDER BY
      CASE churn_risk
        WHEN 'High Risk' THEN 1
        WHEN 'Medium Risk' THEN 2
        ELSE 3
      END,
      days_since_last_purchase DESC,
      spend_last_90_days ASC
    LIMIT 50
    """

    df_churn = run_query(churn_query)

    if not df_churn.empty:
        risk_counts = (
            df_churn.groupby("churn_risk", as_index=False)["hshd_num"]
            .count()
            .rename(columns={"hshd_num": "Household Count", "churn_risk": "Churn Risk"})
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("High-Risk Households", int((df_churn["churn_risk"] == "High Risk").sum()))
        c2.metric("Longest Inactivity", int(df_churn["days_since_last_purchase"].max()))
        c3.metric("Lowest Recent 90-Day Spend", f"${df_churn['spend_last_90_days'].min():,.2f}")

        display_churn = df_churn.rename(columns={
            "hshd_num": "Household Number",
            "loyalty_flag": "Loyalty Flag",
            "days_since_last_purchase": "Days Since Last Purchase",
            "spend_last_90_days": "Recent 90-Day Spend",
            "spend_previous_90_days": "Previous 90-Day Spend",
            "baskets_last_90_days": "Baskets in Last 90 Days",
            "churn_risk": "Churn Risk"
        })

        display_churn["Retention Action"] = display_churn["Churn Risk"].map({
            "High Risk": "Send targeted retention offer immediately",
            "Medium Risk": "Re-engage with category-based promotion",
            "Low Risk": "Maintain regular loyalty communication"
        })

        st.subheader("Households at Risk of Disengaging")
        st.dataframe(display_churn, use_container_width=True)

        st.subheader("Churn Risk Distribution")
        st.bar_chart(risk_counts.set_index("Churn Risk"))

        st.info(
            "Recommended strategy: prioritize high-risk households first, especially those with long inactivity and sharp declines in recent spending."
        )
    else:
        st.warning("No churn data returned.")
