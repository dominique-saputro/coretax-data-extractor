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
from utils import parse_bupots
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = base.BASE_URL

st.set_page_config(page_title="Download Bupot - Dokumen Saya", layout="centered", page_icon="📄")
st.title("📄 Download Bupot - Dokumen Saya")

# --- 1️⃣ Token Validation ---
token = st.session_state.get("token", None)
taxpayer_id = st.session_state.get("taxpayer_id", None)
taxpayer_name = st.session_state.get("taxpayer_name", None)
rep_tin = st.session_state.get("rep_tin", None)
roles = st.session_state.get("roles", None)

base.auth_header(token,taxpayer_id,taxpayer_name)
    
# --- 2️⃣ Parameters ---
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

spt_options = base.get_allowed_roles(roles)
if spt_options['PPN'] is not None:
    spt_options.pop('PPN')
# st.write(spt_options.keys())

period,year,rows = base.parameter_body(month_mapping)
period_num = int(period[:2]) 
spt_choice = st.selectbox(
    "Select SPT",
    options=list(spt_options.keys()),
    index=0 if spt_options else None
)
if spt_choice is not None:
    spt_type = spt_options[spt_choice]['code']
else:
    st.warning("No SPT available for your role.")
    st.stop()  

# --- 3️⃣ Fetch Data ---
if st.button("🔍 Fetch Data from Coretax"):
    status_placeholder = st.empty()
    status_placeholder.info("Fetching data from Coretax API...")
    
    taxperiod = period + str(year)
    
    download_list = []

    url = BASE_URL + "/withholdingslipsportal/api/GetMyWithholdingSlip"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    match spt_choice:
        case 'Unifikasi':
            bupot_type = 'EBUPOTBPU'
        case 'PPh21':
            bupot_type = 'EBUPOTBP21'
    
    payload = {
        "WithholdingType": f"{bupot_type}",
        "TaxPeriod": f"TD.007{period[:2]}",
        "TaxYear":  f"{year}",
        "First": 0,
        "Rows": f"{rows}",
        "SortField": "",
        "SortOrder": 1,
        "Filters": [
            {
                "MatchMode": "equals",
                "PropertyName": "TaxPeriodCode",
                "Value": f"{taxperiod}"
            }
        ],
        "LanguageId": "id-ID",
        "TaxpayerAggregateIdentifier": f"{taxpayer_id}"
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
        if len(records) == 0:
            month_name = reverse_month_mapping[period]
            status_placeholder.empty()
            st.warning(f"No records found for {month_name} {year}")
            st.stop()
            
        details = records
        st.success(f"✅ Success! Retrieved SPT {spt_choice} {reverse_month_mapping[period]} {year} records.")
        status_placeholder.empty()
        
    except requests.exceptions.RequestException as e:
        status_placeholder.empty()
        st.warning(f"⚠️ Failed to retrieve download request: {e}")

# --- 4️⃣ Compile PDF into ZIP ---                
    if details:
        try:
            status_placeholder.empty()
            st.success(f"✅ Fetched details for {len(details)} records.")
            status_placeholder.info("Compiling into Excel...")
            
            detail_data = parse_bupots(spt_choice,details)      
            st.dataframe(detail_data)

            # Export to excel
            excel_buffer = io.BytesIO()
            detail_data.to_excel(excel_buffer, index=False, engine="openpyxl")
            st.download_button(
                "📊 Download Details Excel",
                data=excel_buffer.getvalue(),
                file_name=f"bupot_{spt_choice}_{taxperiod}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            status_placeholder.empty()
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("No details were retrieved.") 
        
    

