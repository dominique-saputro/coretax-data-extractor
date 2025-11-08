import streamlit as st
import requests
import pandas as pd
import io
import time

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

def get_period_end_date(period_code, year):
    """
    Map Coretax TD.007XX period codes to the end-of-month date.
    Example: TD.00709 + 2025 → 30/09/2025
    """
    if not period_code:
        return ""
    try:
        base_date = month_end_map.get(period_code[:8], "")  # first 8 chars e.g. TD.00709
        if base_date and year:
            return f"{year}{base_date}"
        return base_date
    except Exception:
        return ""

st.set_page_config(page_title="Pajak Keluaran", layout="centered", page_icon="📄")
st.title("📄 Lampiran SPT")

# --- 1️⃣ Token Validation ---
st.subheader("Authorization")
token = st.session_state.get("token", None)
taxpayer_id = st.session_state.get("taxpayer_id", None)
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
year = st.number_input("TaxInvoiceYear", value=2025)
rows = st.number_input("Number of Rows", min_value=100, max_value=10000, value=100)

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
        "Rows": 10,
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
            if isinstance(period, list):
                month_names = [reverse_month_mapping[p] for p in period]
                st.warning(f"No records found for {', '.join(month_names)} {year}")
            else:
                month_name = reverse_month_mapping[period]
                st.warning(f"No records found for {month_name} {year}")
            status_placeholder.empty()
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
            df_details = pd.json_normalize(details)
            st.success(f"✅ Fetched details for {len(df_details)} records.")
            
            status_placeholder.info("Compiling into Excel...")
            st.dataframe(details)
            payloads = details
            
    #         all_rows = []
            
    #         column_map = {
    #             "FormDataObj_TransactionDocumentData_InvoiceDate": "tanggal",
    #             "FormDataObj_TransactionDocumentData_TaxInvoiceNumber": "nota",
    #             "BuyerTIN": "relasi",
    #             "kode": "kode",
    #             "qtybox": "qtybox",
    #             "qtylsn": "qtylsn",
    #             "FormDataObj_TransactionDetailsData_Quantity": "qtypcs",
    #             "hrgbox": "hrgbox",
    #             "hrglsn": "hrglsn",
    #             "FormDataObj_TransactionDetailsData_UnitPrice": "hrgpcs",
    #             "FormDataObj_TransactionDetailsData_Discount": "discount",
    #             "FormDataObj_TransactionDetailsData_VATRate": "ppn",
    #             "FormDataObj_TransactionDocumentData_Period": "sptmasa",
    #             "FormDataObj_TransactionDetailsData_TotalPrice": "jmldpp",
    #             "FormDataObj_TransactionDetailsData_VAT": "jmlppn",
    #             "BuyerName": "nmsup",
    #             "FormDataObj_TransactionDetailsData_Name": "nmbrg",
    #             "divisi": "divisi",
    #             "TaxInvoiceNumber": "nofp"
    #         }

    #         month_end_map = {
    #             "TD.00701": "/01/31",
    #             "TD.00702": "/02/28",
    #             "TD.00703": "/03/31",
    #             "TD.00704": "/04/30",
    #             "TD.00705": "/05/31",
    #             "TD.00706": "/06/30",
    #             "TD.00707": "/07/31",
    #             "TD.00708": "/08/31",
    #             "TD.00709": "/09/30",
    #             "TD.00710": "/10/31",
    #             "TD.00711": "/11/30",
    #             "TD.00712": "/12/31",
    #         }

    #         for payload in payloads:  # assume this is your list of invoices
    #             inv_details = payload["FormDataObj"]["TransactionDetailsData"]["Rows"]
    #             for d in inv_details:
    #                 period_code = payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("Period", "")
    #                 year = payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("Year", "")

    #                 sptmasa_value = get_period_end_date(period_code, year)

    #                 row = {
    #                     # pull in detail-level fields
    #                     # "FormDataObj_TransactionDetailsData_Type": d.get("Type", ""),
    #                     "FormDataObj_TransactionDetailsData_Name": d.get("Name", ""),
    #                     # "FormDataObj_TransactionDetailsData_Code": d.get("Code", ""),
    #                     "FormDataObj_TransactionDetailsData_Quantity": d.get("Quantity", 0),
    #                     # "FormDataObj_TransactionDetailsData_Unit": d.get("Unit", ""),
    #                     "FormDataObj_TransactionDetailsData_UnitPrice": d.get("UnitPrice", 0),
    #                     "FormDataObj_TransactionDetailsData_Discount": d.get("Discount", 0),
    #                     "FormDataObj_TransactionDetailsData_VATRate": d.get("VATRate", 0),
    #                     "FormDataObj_TransactionDetailsData_TotalPrice": d.get("TotalPrice", 0),
    #                     "FormDataObj_TransactionDetailsData_VAT": d.get("VAT", 0),

    #                     # include parent-level info from FormDataObj_TransactionDocumentData
    #                     "FormDataObj_TransactionDocumentData_InvoiceDate": payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("InvoiceDate", ""),
    #                     "FormDataObj_TransactionDocumentData_TaxInvoiceNumber": payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("TaxInvoiceNumber", ""),
    #                     "FormDataObj_TransactionDocumentData_Period": sptmasa_value,

    #                     # add seller info
    #                     "BuyerTIN": payload.get("BuyerTIN", ""),
    #                     "BuyerName": payload.get("BuyerName", ""),
    #                     "TaxInvoiceNumber": payload.get("TaxInvoiceNumber", ""),
    #                 }
    #                 all_rows.append(row)

    #         df_all = pd.DataFrame(all_rows)
    #         df_all.rename(columns=column_map, inplace=True)

    #         # Ensure all target columns exist
    #         for col in column_map.values():
    #             if col not in df_all.columns:
    #                 df_all[col] = ""

    #         # Reorder safely
    #         df_all = df_all[list(column_map.values())]
    #         df_all["tanggal"] = df_all["tanggal"].apply(format_date)

    #         # st.write(df_all.columns.tolist())
    #         st.dataframe(df_all)

    #         # Export to excel
    #         excel_buffer = io.BytesIO()
    #         df_all.to_excel(excel_buffer, index=False, engine="openpyxl")
    #         st.download_button(
    #             "📊 Download Details Excel",
    #             data=excel_buffer.getvalue(),
    #             file_name="coretax_output_invoice_details.xlsx",
    #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    #         )
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("No details were retrieved.")   
        
    

