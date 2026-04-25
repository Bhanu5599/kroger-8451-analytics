import os
import streamlit as st
from google.cloud import storage, bigquery
from utils.auth import require_login
from utils.ui import apply_theme

PROJECT_ID = os.getenv("PROJECT_ID", "final-group-project-10")
BUCKET_NAME = os.getenv("BUCKET_NAME", "final_project_retail_data")

require_login()
apply_theme("Latest Data Upload", "Upload refreshed source files and reload BigQuery tables.")

storage_client = storage.Client(project=PROJECT_ID)
bq_client = bigquery.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

def upload_to_gcs(uploaded_file, folder_name):
    blob = bucket.blob(f"raw/{folder_name}/{uploaded_file.name}")
    blob.upload_from_string(uploaded_file.getvalue(), content_type="text/csv")
    return f"gs://{BUCKET_NAME}/{blob.name}"

def load_csv_to_table(gcs_uri, table_name):
    table_id = f"{PROJECT_ID}.retail_analytics.{table_name}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    job = bq_client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    job.result()

def refresh_join_view():
    query = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.retail_analytics.v_retail_joined` AS
    SELECT
      SAFE_CAST(t.`HSHD_NUM        ` AS INT64) AS hshd_num,
      SAFE_CAST(t.`BASKET_NUM                      ` AS INT64) AS basket_num,
      t.`PURCHASE_` AS purchase_date,
      SAFE_CAST(t.`PRODUCT_NUM                     ` AS INT64) AS product_num,
      TRIM(CAST(p.`DEPARTMENT                ` AS STRING)) AS department,
      TRIM(CAST(p.`COMMODITY                 ` AS STRING)) AS commodity,
      TRIM(CAST(p.`BRAND_TY` AS STRING)) AS brand_type,
      CAST(p.`NATURAL_ORGANIC_FLAG` AS STRING) AS natural_organic_flag,
      SAFE_CAST(t.`     SPEND` AS FLOAT64) AS spend,
      SAFE_CAST(t.`     UNITS` AS INT64) AS units,
      TRIM(CAST(t.`STORE_R` AS STRING)) AS store_region,
      SAFE_CAST(t.`  WEEK_NUM` AS INT64) AS week_num,
      SAFE_CAST(t.`YEAR` AS INT64) AS year,
      CAST(h.`L` AS STRING) AS loyalty_flag,
      TRIM(CAST(h.`AGE_RANGE                                                                                                                                                                                               ` AS STRING)) AS age_range,
      TRIM(CAST(h.`MARITAL` AS STRING)) AS marital_status,
      TRIM(CAST(h.`INCOME_RANGE                                                                                                                                                                                            ` AS STRING)) AS income_range,
      TRIM(CAST(h.`HOMEOWNER` AS STRING)) AS homeowner_desc,
      TRIM(CAST(h.`HSHD_COMPOSITION ` AS STRING)) AS hshd_composition,
      SAFE_CAST(h.`HH_SIZE                                                                                                                                                                                                 ` AS INT64) AS hshd_size,
      SAFE_CAST(h.`CHILDREN` AS INT64) AS children
    FROM `{PROJECT_ID}.retail_analytics.transactions` t
    LEFT JOIN `{PROJECT_ID}.retail_analytics.households` h
      ON SAFE_CAST(t.`HSHD_NUM        ` AS INT64) = SAFE_CAST(h.`HSHD_NUM        ` AS INT64)
    LEFT JOIN `{PROJECT_ID}.retail_analytics.products` p
      ON SAFE_CAST(t.`PRODUCT_NUM                     ` AS INT64) = SAFE_CAST(p.`PRODUCT_NUM                     ` AS INT64)
    """
    bq_client.query(query).result()

st.markdown(
    f"""
    <div class="soft-card">
        <h4 style="margin-top:0;">Target bucket</h4>
        <p class="mini-note">{BUCKET_NAME}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)
with c1:
    households_file = st.file_uploader("Households CSV", type=["csv"], key="households")
with c2:
    transactions_file = st.file_uploader("Transactions CSV", type=["csv"], key="transactions")
with c3:
    products_file = st.file_uploader("Products CSV", type=["csv"], key="products")

if st.button("Upload and Refresh Tables", use_container_width=True):
    if not households_file or not transactions_file or not products_file:
        st.error("Upload all three files: households, transactions, and products.")
    else:
        with st.spinner("Uploading files and refreshing BigQuery tables..."):
            h_uri = upload_to_gcs(households_file, "households")
            t_uri = upload_to_gcs(transactions_file, "transactions")
            p_uri = upload_to_gcs(products_file, "products")

            load_csv_to_table(h_uri, "households")
            load_csv_to_table(t_uri, "transactions")
            load_csv_to_table(p_uri, "products")
            refresh_join_view()

        st.success("Upload complete and BigQuery tables refreshed.")

        test_query = f"""
        SELECT COUNT(*) AS row_count
        FROM `{PROJECT_ID}.retail_analytics.v_retail_joined`
        WHERE hshd_num = 10
        """
        df_test = bq_client.query(test_query).to_dataframe()
        st.info(f"HSHD_NUM 10 test rows after refresh: {int(df_test.loc[0, 'row_count'])}")	
