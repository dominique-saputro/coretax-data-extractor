import streamlit as st
import requests
import time
import pandas as pd
from utils import base
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = base.BASE_URL

st.set_page_config(page_title="Download A1", layout="centered", page_icon="📄")
st.title("📄 Download A1")

# --- 1️⃣ Token Validation ---
token = st.session_state.get("token", None)
taxpayer_id = st.session_state.get("taxpayer_id", None)
taxpayer_name = st.session_state.get("taxpayer_name", None)
rep_tin = st.session_state.get("rep_tin", None)
roles = st.session_state.get("roles", None)

base.auth_header(token,taxpayer_id,taxpayer_name)
    
# --- 2️⃣ Parameters ---
roles = set(roles)
month_mapping = {
    "January": "0101",
    "February": "0202",
    "March": "0303",
    "April": "0404",
    "May": "0505",
    "June": "0606",
    "July": "0707",
    "August": "0808",
    "September": "0909",
    "October": "1010",
    "November": "1111",
    "December": "1212",
}
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
    # "Unifikasi": "ICT_WT",
    "A1":"ICT_WIT"
}

period,year,rows = base.parameter_body(month_mapping)
period_num = int(period[:2]) 
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
    taxperiods = [
        code + str(year)
        for code in month_mapping.values()
    ]

    url = BASE_URL + "/withholdingslipsportal/api/getebupotbpa1issued"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    } 
    
    for taxperiod in taxperiods:
        payload = {
            "First": 0,
            "Rows": rows,
            "SortField": "",
            "SortOrder": 1,
            "Filters": [
                {
                    "PropertyName": "IncomePeriodCodeEnd",
                    "Value": f"{taxperiod}",
                    "MatchMode": "equals",
                    "CaseSensitive": True,
                    "AsString": False
                }
            ],
            "LanguageId": "id-ID",
            "TaxpayerAggregateIdentifier": f"{taxpayer_id}",
        }

        try:
            # st.write(payload)
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            records = data.get("Payload", {}).get("Data", [])
            df = pd.json_normalize(records)
            
            # extract RecordIds from DataFrame
            reverse_month_mapping = {v: k for k, v in month_mapping.items()}
            if len(records) > 0:   
                wanted_keys = {
                    "WithholdingslipsAggregateIdentifier",
                    "RecordId",
                    "DocumentFormAggregateIdentifier",
                    "LastUpdatedDate",
                    "TaxIdentificationNumber",
                    "Name"
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

    url = BASE_URL + "/withholdingslipsportal/api/DownloadWithholdingSlips/download-pdf-document"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    def download_pdf(row):
        payload = {
            "WithholdingSlipsAggregateIdentifier": row["WithholdingslipsAggregateIdentifier"],
            "WithholdingSlipsRecordIdentifier": row["RecordId"],
            "DocumentAggregateIdentifier": row["DocumentFormAggregateIdentifier"],
            "TaxpayerAggregateIdentifier": taxpayer_id,
            "EbupotType": "EBUPOTBPA1",
            "DocumentDate": row["LastUpdatedDate"],
            "TaxIdentificationNumber": row["TaxIdentificationNumber"],
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

                data = resp.json()
                content = data.get("Content")
                filename = f"{row['Name']}.pdf"

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
            st.warning(f"{i+1}. {fail["TaxIdentificationNumber"]} - {fail["Name"]}")
    st.success(f"✅ Downloaded {len(details)} files successfully")



#     status_placeholder.info("Starting download from Coretax API...")
#     total = len(download_list)
#     progress_bar = st.progress(0)
#     status_text = st.empty()
#     details = []
#     fails = []
#     url = BASE_URL + "/withholdingslipsportal/api/DownloadWithholdingSlips/download-pdf-document"
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }
#     try:    
#         for i, row in enumerate(download_list, start=1):
#             status_text.info(f"Fetching file {i}/{total}")
            
#             payload = {
#                 "WithholdingSlipsAggregateIdentifier": f"{row['WithholdingslipsAggregateIdentifier']}",
#                 "WithholdingSlipsRecordIdentifier": f"{row['RecordId']}",
#                 "DocumentAggregateIdentifier": f"{row['DocumentFormAggregateIdentifier']}",
#                 "TaxpayerAggregateIdentifier": f"{taxpayer_id}",
#                 "EbupotType": "EBUPOTBPA1",
#                 "DocumentDate": f"{row['LastUpdatedDate']}",
#                 "TaxIdentificationNumber": f"{row['TaxIdentificationNumber']}",
#             }

#             try:
#                 resp = requests.post(url, headers=headers, json=payload,timeout=(10, 120))
#                 resp.raise_for_status()
#                 detail_data = resp.json()
                
#                 content = detail_data.get("Content")
#                 filename = f"{row['Name']}.pdf" 

#                 if content and filename:
#                     details.append({
#                         "Content": content,
#                         "FileName": filename
#                     })
                    
#             except requests.exceptions.RequestException as e:
#                 status_placeholder.empty()
#                 st.warning(f"⚠️ Failed to fetch PDF: {e}")
#                 fails.append(row)
            
#             progress_bar.progress(i / total)
            
#         status_text.empty()
#         progress_bar.empty()       
#     except requests.exceptions.RequestException as e:
#         status_placeholder.empty()
#         st.error(f"Request failed: {e}")

# --- 4️⃣ Compile PDF into ZIP ---                
    if details:
        try:
            status_placeholder.empty()
            status_placeholder.info("Compiling into zip file...")
            
            zip_buffer = base.build_zip_in_memory(details)
            
            st.download_button(
                "📁 Download Bupot A1",
                data=zip_buffer,
                file_name="bupot_a1.zip",
                mime="application/zip"
            )
            status_placeholder.empty()
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("No details were retrieved.")   
        
    

