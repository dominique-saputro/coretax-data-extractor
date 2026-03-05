import streamlit as st
import requests
import time
import datetime
import calendar
import pandas as pd
import io
import zipfile
import base64
from utils import base
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = base.BASE_URL

st.set_page_config(page_title="Download BPPU", layout="centered", page_icon="📄")
st.title("📄 Download BPPU")

# --- 1️⃣ Token Validation ---
token = st.session_state.get("token", None)
taxpayer_id = st.session_state.get("taxpayer_id", None)
taxpayer_name = st.session_state.get("taxpayer_name", None)
rep_tin = st.session_state.get("rep_tin", None)
roles = st.session_state.get("roles", None)

base.auth_header(token,taxpayer_id,taxpayer_name)
    
# --- 2️⃣ Parameters ---
roles = set(roles)
spt_options = {}
ROLE_SPT_MAPPING = {
    "PPN": {
        "role": 32,
        "code": "VAT_VAT"
    },
    "Unifikasi": {
        "role": 38,
        "code": "ICT_WT"
    },
    "PPh21": {
        "role": 42,
        "code": "ICT_WIT"
    }
}
for name, info in ROLE_SPT_MAPPING.items():
    st.session_state[f"allow_{name.lower()}"] = info["role"] in roles
    if info["role"] in roles:
        spt_options[name] = info["code"]   
spt_options = {
    # "PPN": "VAT_VAT",
    "Unifikasi": "ICT_WT",
    # "A1":"ICT_WIT"
}
today = datetime.datetime.now()
_, last_day = calendar.monthrange(today.year, today.month)

st.subheader("Query Parameters")
date = st.date_input(
    "Select date range",
    (datetime.date(today.year,today.month,1),datetime.date(today.year,today.month,last_day)),
    format="YYYY/MM/DD")
spt_choice = st.selectbox(
    "Select Bupot",
    options=list(spt_options.keys()),
    index=0 if spt_options else None
)
if spt_choice is not None:
    spt_type = spt_options[spt_choice]
else:
    st.warning("Not authorized for your role.")
    st.stop()

# --- 3️⃣ Fetch Data ---
if st.button("🔍 Fetch Data from Coretax"):
    status_placeholder = st.empty()
    status_placeholder.info("Fetching data from Coretax API...")
    
    download_list = []

    url = BASE_URL + "/documentmanagementportal/api/list/listTaxpayerDocuments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    } 
    
    payload = {
        "TaxpayerAggregateIdentifier": f"{taxpayer_id}",
        "IsCaseCompleted": True,
        "IsSkipInvoiceDocument": False,
        "First": 0,
        "Rows": 10000,
        "SortField": "CreationDatetime",
        "SortOrder": 1,
        "Filters": [
            {
                "PropertyName": "DocumentDate",
                "Value": [
                    f"{date[0].strftime("%Y/%m/%d")}",
                    f"{date[1].strftime("%Y/%m/%d")}"
                ],
                "MatchMode": "between",
                "CaseSensitive": True,
                "AsString": False
            },
            {
                "PropertyName": "DocumentTitle",
                "Value": "Bukti Potong PPh Unifikasi (BPPU)",
                "MatchMode": "startsWith",
                "CaseSensitive": False,
                "AsString": False
            }
        ],
        "LanguageId": "id-ID"
    }

    try:
        # st.write(payload)
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        records = data.get("Payload", {}).get("Data", [])
        df = pd.json_normalize(records)
        
        # extract RecordIds from DataFrame
        if len(records) > 0:   
            wanted_keys = {
                "AggregateIdentifier",
                "DocumentNumber",
                "LetterNumber",
            }

            download_list.extend(
                {k: r.get(k) for k in wanted_keys}
                for r in records
            )
        
    except requests.exceptions.RequestException as e:
        status_placeholder.empty()
        st.warning(f"⚠️ Failed to retrieve download request: {e}")
        
                   
    st.success(f"✅ Success! Retrieved download request {len(download_list)} files.")
    status_placeholder.empty()
    # st.write(download_list)
        
    # get details for all months
    MAX_WORKERS = 3
    MAX_RETRIES = 3

    status_placeholder.info("Starting download from Coretax API...")

    total = len(download_list)
    progress_bar = st.progress(0)
    status_text = st.empty()

    details = []
    fails = []

    url = BASE_URL + "/documentmanagementportal/api/download"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    def download_pdf(row):
        payload = {
            "DocumentId": row["DocumentNumber"],
            "TaxpayerAggregateIdentifier": f"{taxpayer_id}",
            "IsNeedWatermark": True,
            "FormCallerName": "TaxpayerDocuments",
            "DocumentAggregateIdentifier": row["AggregateIdentifier"]
        }

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=(10, 120),
                )
                resp.raise_for_status()

                content = resp.content
                filename = f"{row['LetterNumber']}.pdf"

                if not content:
                    raise ValueError("Empty PDF content")

                return {
                    "success": True,
                    "data": {
                        "Content": content,
                        "FileName": filename,
                    },
                }

            except Exception as e:
                if attempt == MAX_RETRIES:
                    return {
                        "success": False,
                        "row": row,
                        "error": str(e),
                    }

                time.sleep(1 * attempt)  # simple backoff
                
    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(download_pdf, row)
            for row in download_list
        ]

        for future in as_completed(futures):
            result = future.result()
            completed += 1

            status_text.info(f"Fetching file {completed}/{total}")
            progress_bar.progress(completed / total)

            if result["success"]:
                details.append(result["data"])
            else:
                fails.append(result["row"])
    
    status_text.empty()
    progress_bar.empty()

    if fails:
        st.warning(f"⚠️ {len(fails)} Bupot gagal download, Coba download manual untuk:")
        for i,fail in enumerate(fails):
            st.warning(f"{i+1}. {fail["LetterNumber"]}")
    st.success(f"✅ Downloaded {len(details)} files successfully")

# --- 4️⃣ Compile PDF into ZIP ---                
    if details:
        try:
            status_placeholder.empty()
            status_placeholder.info("Compiling into zip file...")
            
            zip_buffer = io.BytesIO()
            total = len(details)

            progress = st.progress(0)
            status = st.empty()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for i,r in enumerate(details, start=1):
                    status.info(f"Zipping {i}/{total}")
                    pdf_bytes = r["Content"]
                    filename = r.get("FileName", "file.pdf")
                    zipf.writestr(filename, pdf_bytes)
                    progress.progress(i / total)

            status.empty()
            progress.empty()

            zip_buffer.seek(0)
            
            st.download_button(
                "📁 Download Bupot Unifikasi",
                data=zip_buffer,
                file_name="bupot_uni.zip",
                mime="application/zip"
            )
            status_placeholder.empty()
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("No details were retrieved.")   
        
    

