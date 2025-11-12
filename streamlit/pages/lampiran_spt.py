import streamlit as st
import requests
import pandas as pd
import io
import time
from utils import parse_lampiran

BASE_URL = "https://coretaxdjp.pajak.go.id"

def keepalive(token):
    """Ping the Coretax KeepAlive endpoint to maintain session"""
    url = BASE_URL + "/identityproviderportal/api/Account/SessionKeepAlive"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        time.sleep(0.5)
        resp = requests.post(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            st.write("💓 Session refreshed (KeepAlive successful).")
        else:
            st.warning(f"KeepAlive failed: {resp.status_code}")
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ KeepAlive error: {e}")

def format_date(date_str):
    """Convert ISO date string (2025-09-17T00:00:00) to YYYY/MM/DD format."""
    try:
        return pd.to_datetime(date_str).strftime("%Y/%m/%d")
    except Exception:
        return ""

st.set_page_config(page_title="Lampiran SPT", layout="centered", page_icon="📄")
st.title("📄 Lampiran SPT")

# --- 1️⃣ Token Validation ---
token = st.session_state.get("token", None)
taxpayer_id = st.session_state.get("taxpayer_id", None)
taxpayer_name = st.session_state.get("taxpayer_name", None)
st.subheader(f"Authorization - {taxpayer_name}")
if token and taxpayer_id:
    keepalive(token)
else:
    if not token:
        st.warning("Token invalid.")
    if not taxpayer_id:
        st.warning("Taxpayer Id not found.")
    
# --- 2️⃣ Parameters ---
st.subheader("Query Parameters")
spt_options = {
    "PPN":"VAT_VAT",
    "PPh21":"ICT_WIT",
    "Unifikasi":"ICT_WT",
}
spt_choice = st.selectbox(
    "Select SPT",
    options=list(spt_options.keys()),
)
spt_type = spt_options[spt_choice]
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
months = st.selectbox(
    "Select month(s) for TaxInvoicePeriod",
    options=list(month_mapping.keys()),
)
period = month_mapping[months]
period_num = int(period[:2]) 
year = st.number_input("TaxInvoiceYear", value=2025)
rows = st.number_input("Number of Rows", min_value=100, max_value=10000, value=100, step=50)

# --- 3️⃣ Fetch Data ---
if st.button("🔍 Fetch Data from Coretax"):
    status_placeholder = st.empty()
    status_placeholder.info("Fetching data from Coretax API...")
    
    taxperiod = period + str(year)
   
    url = BASE_URL + "/returnsheetportal/api/returnsheetssubmitted"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    } 
    payload = {
        "TaxpayerAggregateIdentifier": f"{taxpayer_id}",
        "isArchieved": False,
        "First": 0,
        "Rows": rows,
        "SortField": "",
        "SortOrder": 1,
        "Filters": [
            {
                "PropertyName": "TaxTypeCode",
                "Value": [
                    f"{spt_type}"
                ],
                "MatchMode": "contains",
                "CaseSensitive": True,
                "AsString": False
            },
            {
                "PropertyName": "TaxPeriodCode",
                "Value": f"{taxperiod}",
                "MatchMode": "equals",
                "CaseSensitive": True,
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
        reverse_month_mapping = {v: k for k, v in month_mapping.items()}
        if len(records) == 0:
            month_name = reverse_month_mapping[period]
            status_placeholder.empty()
            st.warning(f"No records found for {month_name} {year}")
            st.stop()
            
        record_ids = df["RecordId"].dropna().tolist()
        st.success(f"✅ Success! Retrieved SPT {spt_choice} {reverse_month_mapping[period]} {year} records.")
        status_placeholder.empty()
        
        # get details for all headers
        status_placeholder.info("Fetching details from Coretax API...")
        details = []
        match spt_choice:
            case 'PPN':
                api_urls = [
                    "/returnsheetportal/api/loadndvat/la1-grid",
                    "/returnsheetportal/api/loadndvat/la2-grid",
                    "/returnsheetportal/api/loadndvat/lb1-grid",
                    "/returnsheetportal/api/loadndvat/lb2-grid",
                    "/returnsheetportal/api/loadndvat/lb3-grid",
                ]
            case 'PPh21':
                api_urls = [
                    "/returnsheetportal/api/loadarticle2126/l1a-grid",
                    "/returnsheetportal/api/loadarticle2126/l3-bp21-grid"
                ]
            case 'Unifikasi':
                api_urls = [
                    "/returnsheetportal/api/loadwtr/list-i-bpu-grid"
                ]
        for i, rid in enumerate(record_ids):
            for api_url in api_urls:
                # Ping KeepAlive every 10 requests
                if i % 10 == 0:
                    keepalive(token)
                    
                url = BASE_URL + api_url
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                if spt_choice == 'PPN':
                    payload = {
                        "ReturnSheetRecordId": f"{rid}",
                        "IsNormalVAT": True,
                        "First": 0,
                        "Rows": rows,
                        "SortField": "",
                        "SortOrder": 1,
                        "Filters": [],
                        "LanguageId": "id-ID",
                        "TaxpayerAggregateIdentifier": f"{taxpayer_id}"
                    }
                else:
                    payload = {
                        "ReturnSheetRecordId": f"{rid}",
                        "First": 0,
                        "Rows": rows,
                        "SortField": "",
                        "SortOrder": 1,
                        "Filters": [],
                        "LanguageId": "id-ID",
                        "TaxpayerAggregateIdentifier": f"{taxpayer_id}"
                    }

                try:
                    resp = requests.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    detail_data = resp.json()
                    
                    if len(detail_data) == 0:
                        details.append('')
                    else:
                        details.append(detail_data.get("Payload", detail_data))
                        
                except requests.exceptions.RequestException as e:
                    status_placeholder.empty()
                    st.warning(f"⚠️ Failed to fetch details for RecordId {rid}: {e}")
                
    except requests.exceptions.RequestException as e:
        status_placeholder.empty()
        st.error(f"Request failed: {e}")

# --- 4️⃣ Process Data into Excel ---                
    if details:
        try:
            status_placeholder.empty()
            st.success(f"✅ Fetched details for {len(details)} records.")
            status_placeholder.info("Compiling into Excel...")
            
            dfs = parse_lampiran(spt_choice,details)
            for name, df in dfs.items():
                if not df.empty:
                    df.insert(0, "Masa", period_num)  
                    
            # Summary        
            # st.dataframe(details)
            # st.dataframe(dfs["DAFTAR-I"])
            summary = pd.DataFrame([
                {"Sheet Name": name, "Record Count": len(df)}
                for name, df in dfs.items()
            ])

            st.dataframe(summary)

            # Export to excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for sheet_name, dataframe in dfs.items():
                    dataframe.to_excel(writer, index=False, sheet_name=sheet_name)
            st.download_button(
                "📊 Download Details Excel",
                data=output.getvalue(),
                file_name=f"{spt_choice}_lampiran_details.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            status_placeholder.empty()
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("No details were retrieved.")   
        
    

