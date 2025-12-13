import streamlit as st
import requests
import pandas as pd
import io
from utils import base

BASE_URL = base.BASE_URL

st.set_page_config(page_title="Pajak Keluaran", layout="centered", page_icon="⚖️")
st.title("⚖️ Pajak Keluaran")

# --- 1️⃣ Token Validation ---
token = st.session_state.get("token", None)
taxpayer_id = st.session_state.get("taxpayer_id", None)
taxpayer_name = st.session_state.get("taxpayer_name", None)
base.auth_header(token,taxpayer_id,taxpayer_name)
    
# --- 2️⃣ Parameters ---
period,year,rows = base.parameter_body()
current_params = {
    "period": tuple(period),  # list → tuple (hashable)
    "year": year,
    "rows": rows,
}
if "last_params" not in st.session_state:
    st.session_state.last_params = current_params
else:
    if st.session_state.last_params != current_params:
        for key in ["cursor", "details", "fails"]:
            st.session_state.pop(key, None)

        st.session_state.last_params = current_params
        st.info("🔄 Parameters changed — progress reset.")

# --- 3️⃣ Fetch Data ---
if st.button("🔍 Fetch Data from Coretax"):
    status_placeholder = st.empty()
    status_placeholder.info("Fetching data from Coretax API...")
   
    url = BASE_URL + "/einvoiceportal/api/outputinvoice/list"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    } 
    payload = {
        "SellerTaxpayerAggregateIdentifier": f"{taxpayer_id}",
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
                "Value": "APPROVED",
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
            month_name  = base.reverse_month_mapping(period)
            status_placeholder.empty()
            st.warning(f"No records found for {month_name} {year}")
            st.stop()
            
        record_ids = df["RecordId"].dropna().tolist()
        st.success(f"✅ Success! Retrieved {len(record_ids)} records.")
        status_placeholder.empty()
        
        # get details for all headers
        url = BASE_URL + "/einvoiceportal/api/outputinvoice/view"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        details = base.fetch_details(record_ids,token,taxpayer_id,url,headers)

    except requests.exceptions.RequestException as e:
        status_placeholder.empty()
        st.error(f"Request failed: {e}")

# --- 4️⃣ Process Data into Excel ---                
    if details:
        try:
            status_placeholder.empty()
            df_details = pd.json_normalize(details)
            st.success(f"✅ Fetched details for {len(df_details)} records.")
            # st.dataframe(details)
            status_placeholder.info("Compiling into Excel...")
            payloads = details
            
            all_rows = []
            
            column_map = {
                "FormDataObj_TransactionDocumentData_InvoiceDate": "tanggal",
                "FormDataObj_TransactionDocumentData_TaxInvoiceNumber": "nota",
                "BuyerTIN": "relasi",
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
                "jmldpp": "jmldpp",
                "FormDataObj_TransactionDetailsData_VAT": "jmlppn",
                "BuyerName": "nmsup",
                "FormDataObj_TransactionDetailsData_Name": "nmbrg",
                "divisi": "divisi",
                "FormDataObj_TransactionDocumentData_Reference": "ref"
            }

            for payload in payloads:  # assume this is your list of invoices
                inv_details = payload["FormDataObj"]["TransactionDetailsData"]["Rows"]
                for d in inv_details:
                    period_code = payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("Period", "")
                    year = payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("Year", "")

                    sptmasa_value = base.get_period_end_date(period_code, year)

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
                        # "FormDataObj_TransactionDetailsData_TaxBase": d.get("TaxBase", 0),
                        "FormDataObj_TransactionDetailsData_VAT": d.get("VAT", 0),

                        # include parent-level info from FormDataObj_TransactionDocumentData
                        "FormDataObj_TransactionDocumentData_InvoiceDate": payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("InvoiceDate", ""),
                        "FormDataObj_TransactionDocumentData_TaxInvoiceNumber": payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("TaxInvoiceNumber", ""),
                        "FormDataObj_TransactionDocumentData_Reference": payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("Reference", ""),
                        "FormDataObj_TransactionDocumentData_Period": sptmasa_value,

                        # add seller info
                        "BuyerTIN": payload.get("BuyerTIN", ""),
                        "BuyerName": payload.get("BuyerName", ""),
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
            df_all["tanggal"] = df_all["tanggal"].apply(base.format_date)
            df_all["jmldpp"] = (df_all["hrgpcs"] * df_all["qtypcs"]) - df_all["discount"]

            # st.write(df_all.columns.tolist())
            status_placeholder.empty()
            st.dataframe(df_all)

            # Export to excel
            excel_buffer = io.BytesIO()
            df_all.to_excel(excel_buffer, index=False, engine="openpyxl")
            st.download_button(
                "📊 Download Details Excel",
                data=excel_buffer.getvalue(),
                file_name="coretax_output_invoice_details.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            status_placeholder.empty()
            st.error(f"Error: {e}")
    else:
        status_placeholder.empty()
        st.warning("No details were retrieved.")   
        
    

