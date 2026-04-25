import os
import streamlit as st
from google.cloud import storage, bigquery
from utils.auth import require_login
from utils.ui import apply_theme

PROJECT_ID = os.getenv("PROJECT_ID", "final-group-project-10")
BUCKET_NAME = os.getenv("BUCKET_NAME", "final_project_retail_data")

require_login()
apply_theme("Latest Data Upload", "Reload the default 84.51° sample dataset or upload refreshed source files.")

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

def run_refresh(households_uri, transactions_uri, products_uri):
    load_csv_to_table(households_uri, "households")
    load_csv_to_table(transactions_uri, "transactions")
    load_csv_to_table(products_uri, "products")
    refresh_join_view()

def test_household_10():
    test_query = f"""
    SELECT COUNT(*) AS row_count
    FROM `{PROJECT_ID}.retail_analytics.v_retail_joined`
    WHERE hshd_num = 10
    """
    return bq_client.query(test_query).to_dataframe()

st.markdown(
    f"""
    <div class="soft-card">
        <h4 style="margin-top:0;">Target bucket</h4>
        <p class="mini-note">{BUCKET_NAME}</p>
    </div>
    """,
    unsafe_allow_html=True,
)


default_households = f"gs://{BUCKET_NAME}/raw/households/400_households.csv"
default_transactions = f"gs://{BUCKET_NAME}/raw/transactions/400_transactions.csv"
default_products = f"gs://{BUCKET_NAME}/raw/products/400_products.csv"

if st.button("Load Default 84.51° Sample Data", use_container_width=True):
    with st.spinner("Reloading default sample dataset into BigQuery..."):
        run_refresh(default_households, default_transactions, default_products)
        df_test = test_household_10()

    st.success("Default sample dataset loaded successfully.")
    st.info(f"HSHD_NUM 10 rows available after reload: {int(df_test.loc[0, 'row_count'])}")
    st.caption("The user can now open Household Data Pull and test HSHD_NUM = 10.")

st.divider()

tab1, tab2 = st.tabs(["Direct Upload", "Refresh from GCS Paths"])

with tab1:
    st.subheader("Direct upload for smaller files")
    st.caption("Use this for smaller files. Large transaction files may exceed Cloud Run upload limits.")

    c1, c2, c3 = st.columns(3)
    with c1:
        households_file = st.file_uploader("Households CSV", type=["csv"], key="households")
    with c2:
        transactions_file = st.file_uploader("Transactions CSV", type=["csv"], key="transactions")
    with c3:
        products_file = st.file_uploader("Products CSV", type=["csv"], key="products")

    if st.button("Upload Selected Files to Cloud Storage", use_container_width=True):
        uploaded = []

        for uploaded_file, folder in [
            (households_file, "households"),
            (transactions_file, "transactions"),
            (products_file, "products"),
        ]:
            if uploaded_file:
                gcs_uri = upload_to_gcs(uploaded_file, folder)
                uploaded.append(gcs_uri)

        if uploaded:
            st.success("Files uploaded to Cloud Storage.")
            for uri in uploaded:
                st.write(uri)
        else:
            st.error("Please upload at least one file.")

with tab2:
    st.subheader("Refresh tables from Cloud Storage paths")
    st.caption("Use this when files already exist in the bucket.")

    households_uri = st.text_input("Households GCS URI", value=default_households)
    transactions_uri = st.text_input("Transactions GCS URI", value=default_transactions)
    products_uri = st.text_input("Products GCS URI", value=default_products)

    if st.button("Refresh BigQuery Tables", use_container_width=True):
        if not households_uri or not transactions_uri or not products_uri:
            st.error("Provide all three GCS paths.")
        else:
            with st.spinner("Refreshing BigQuery tables from Cloud Storage..."):
                run_refresh(households_uri, transactions_uri, products_uri)
                df_test = test_household_10()

            st.success("BigQuery tables refreshed successfully.")
            st.info(f"HSHD_NUM 10 test rows after refresh: {int(df_test.loc[0, 'row_count'])}")

st.subheader("Recent Raw Files in Cloud Storage")
blobs = list(storage_client.list_blobs(BUCKET_NAME, prefix="raw/", max_results=20))
if blobs:
    st.dataframe(
        [{"name": b.name, "size_bytes": b.size} for b in blobs],
        use_container_width=True
    )
else:
    st.info("No raw files found yet.")
