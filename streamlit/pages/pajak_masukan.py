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

st.set_page_config(page_title="Pajak Masukan", layout="centered", page_icon="⚖️")
st.title("⚖️ Pajak Masukan")

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
month_mapping = {
    "January": "TD.00701",
    "February": "TD.00702",
    "March": "TD.00703",
    "April": "TD.00704",
    "May": "TD.00705",
    "June": "TD.00706",
    "July": "TD.00707",
    "August": "TD.00708",
    "September": "TD.00709",
    "October": "TD.00710",
    "November": "TD.00711",
    "December": "TD.00712",
}
months = st.multiselect(
    "Select month(s) for TaxInvoicePeriod",
    options=list(month_mapping.keys()),
    default=["September"]
)
period = [month_mapping[m] for m in months]
year = st.number_input("TaxInvoiceYear", value=2025)
rows = st.number_input("Number of Rows", min_value=100, max_value=10000, value=100, step=50)

# --- 3️⃣ Fetch Data ---
if st.button("🔍 Fetch Data from Coretax"):
    status_placeholder = st.empty()
    status_placeholder.info("Fetching data from Coretax API...")
            
    url = BASE_URL + "/einvoiceportal/api/inputinvoice/list"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    } 
    payload = {
        "BuyerTaxpayerAggregateIdentifier": f"{taxpayer_id}",
        "First": 0,
        "Rows": rows,
        "SortField": "",
        "SortOrder": 1,
        "Filters": [
            {
                "PropertyName": "TaxInvoicePeriod",
                "Value": period,
                "MatchMode": "contains",
                "CaseSensitive": True,
                "AsString": False
            },
            {
                "PropertyName": "TaxInvoiceYear",
                "Value": 2025,
                "MatchMode": "equals",
                "CaseSensitive": True,
                "AsString": False
            },
            {
                "PropertyName": "TaxInvoiceStatus",
                "Value": "CREDITED",
                "MatchMode": "equals",
                "CaseSensitive": True,
                "AsString": False
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
        if len(records) == 0:
            reverse_month_mapping = {v: k for k, v in month_mapping.items()}
            if isinstance(period, list):
                month_names = [reverse_month_mapping[p] for p in period]
                st.warning(f"No records found for {', '.join(month_names)}")
            else:
                month_name = reverse_month_mapping[period]
                st.warning(f"No records found for {month_name}")
            status_placeholder.empty()
            st.stop()
        record_ids = df["RecordId"].dropna().tolist()
        status_placeholder.empty()
        st.success(f"✅ Success! Retrieved {len(record_ids)} records.")
        
        # get details for all headers
        status_placeholder.info("Fetching details from Coretax API...")
        details = []
        for i, rid in enumerate(record_ids):
            # Ping KeepAlive every 10 requests
            if i % 10 == 0:
                keepalive(token)
                
            url = BASE_URL + "/einvoiceportal/api/inputinvoice/view"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "RecordIdentifier": f"{rid}",
                "EinvoiceVATStatus": "",
                "TaxpayerAggregateIdentifier": f"{taxpayer_id}"
            }

            try:
                resp = requests.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                detail_data = resp.json()

                # Optional: append only the "Payload" or "Data" portion
                details.append(detail_data.get("Payload", detail_data))
                # st.write(detail_data)

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
            # st.dataframe(df_details)
            status_placeholder.info("Compiling into Excel...")
            payloads = details
            
            all_rows = []
            
            column_map = {
                "FormDataObj_TransactionDocumentData_InvoiceDate": "tanggal",
                "FormDataObj_TransactionDocumentData_TaxInvoiceNumber": "nota",
                "SellerTIN": "relasi",
                "kode": "kode",
                "qtybox": "qtybox",
                "qtylsn": "qtylsn",
                "FormDataObj_TransactionDetailsData_Quantity": "qtypcs",
                "hrgbox": "hrgbox",
                "hrglsn": "hrglsn",
                "FormDataObj_TransactionDetailsData_UnitPrice": "hrgpcs",
                "FormDataObj_TransactionDetailsData_Discount": "discount",
                "FormDataObj_TransactionDetailsData_VATRate": "ppn",
                "FormDataObj_TransactionDocumentData_Period": "sptmasa",
                "FormDataObj_TransactionDetailsData_TaxBaseTotal": "jmldpp",
                "FormDataObj_TransactionDetailsData_VAT": "jmlppn",
                "SellerName": "nmsup",
                "FormDataObj_TransactionDetailsData_Name": "nmbrg",
                "divisi": "divisi",
                "TaxInvoiceNumber": "nofp"
            }

            month_end_map = {
                "TD.00701": "/01/31",
                "TD.00702": "/02/28",
                "TD.00703": "/03/31",
                "TD.00704": "/04/30",
                "TD.00705": "/05/31",
                "TD.00706": "/06/30",
                "TD.00707": "/07/31",
                "TD.00708": "/08/31",
                "TD.00709": "/09/30",
                "TD.00710": "/10/31",
                "TD.00711": "/11/30",
                "TD.00712": "/12/31",
            }

            for payload in payloads:  # assume this is your list of invoices
                inv_details = payload["FormDataObj"]["TransactionDetailsData"]["Rows"]
                for d in inv_details:
                    period_code = payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("Period", "")
                    year = payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("Year", "")

                    sptmasa_value = get_period_end_date(period_code, year)

                    row = {
                        # pull in detail-level fields
                        # "FormDataObj_TransactionDetailsData_Type": d.get("Type", ""),
                        "FormDataObj_TransactionDetailsData_Name": d.get("Name", ""),
                        # "FormDataObj_TransactionDetailsData_Code": d.get("Code", ""),
                        "FormDataObj_TransactionDetailsData_Quantity": d.get("Quantity", 0),
                        # "FormDataObj_TransactionDetailsData_Unit": d.get("Unit", ""),
                        "FormDataObj_TransactionDetailsData_UnitPrice": d.get("UnitPrice", 0),
                        "FormDataObj_TransactionDetailsData_Discount": d.get("Discount", 0),
                        "FormDataObj_TransactionDetailsData_VATRate": d.get("VATRate", 0),
                        "FormDataObj_TransactionDetailsData_TaxBaseTotal": d.get("TaxBaseTotal", 0),
                        "FormDataObj_TransactionDetailsData_VAT": d.get("VAT", 0),

                        # include parent-level info from FormDataObj_TransactionDocumentData
                        "FormDataObj_TransactionDocumentData_InvoiceDate": payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("InvoiceDate", ""),
                        "FormDataObj_TransactionDocumentData_TaxInvoiceNumber": payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("TaxInvoiceNumber", ""),
                        "FormDataObj_TransactionDocumentData_Period": sptmasa_value,

                        # add seller info
                        "SellerTIN": payload.get("SellerTIN", ""),
                        "SellerName": payload.get("SellerName", ""),
                        "TaxInvoiceNumber": payload.get("TaxInvoiceNumber", ""),
                    }
                    all_rows.append(row)

            df_all = pd.DataFrame(all_rows)
            df_all.rename(columns=column_map, inplace=True)

            # Ensure all target columns exist
            for col in column_map.values():
                if col not in df_all.columns:
                    df_all[col] = ""

            # Reorder safely
            df_all = df_all[list(column_map.values())]
            df_all["tanggal"] = df_all["tanggal"].apply(format_date)

            # st.write(df_all.columns.tolist())
            status_placeholder.empty()
            st.dataframe(df_all)

            # Export to excel
            excel_buffer = io.BytesIO()
            df_all.to_excel(excel_buffer, index=False, engine="openpyxl")
            st.download_button(
                "📊 Download Details Excel",
                data=excel_buffer.getvalue(),
                file_name="coretax_input_invoice_details.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            status_placeholder.empty()
            st.error(f"Error: {e}")
    else:
        status_placeholder.empty()
        st.warning("No details were retrieved.")   
        
    

