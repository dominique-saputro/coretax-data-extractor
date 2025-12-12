import streamlit as st
import requests
import pandas as pd
import io
from utils import base

BASE_URL = base.BASE_URL

st.set_page_config(page_title="Retur Masukan", layout="centered", page_icon="⚖️")
st.title("⚖️ Retur Masukan")

# --- 1️⃣ Token Validation ---
token = st.session_state.get("token", None)
taxpayer_id = st.session_state.get("taxpayer_id", None)
taxpayer_name = st.session_state.get("taxpayer_name", None)
base.auth_header(token,taxpayer_id,taxpayer_name)
    
# --- 2️⃣ Parameters ---
period,year,rows = base.parameter_body()

# --- 3️⃣ Fetch Data ---
if st.button("🔍 Fetch Data from Coretax"):
    status_placeholder = st.empty()
    status_placeholder.info("Fetching data from Coretax API...")
            
    url = BASE_URL + "/einvoiceportal/api/inputreturn/list"
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
        status_placeholder.empty()
        st.success(f"✅ Success! Retrieved {len(record_ids)} records.")
        
        # get details for all headers
        with st.status("Fetching details...", expanded=True) as status:
            details = []
            fails = []
            new_fails = []
            
            url = BASE_URL + "/einvoiceportal/api/inputreturn/view"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
                
            details,fails = base.fetch_details(status,details,fails,record_ids,token,taxpayer_id,url,headers)
            
            MAX_RETRIES = base.MAX_RETRIES
            retry_count = 0

            while len(fails) > 0 and retry_count < MAX_RETRIES:
                retry_count += 1
                st.info(f"Retrying {len(fails)} failed records... Attempt {retry_count}/{MAX_RETRIES}")

                details,new_fails = base.fetch_details(status,details,new_fails,fails,token,taxpayer_id,url,headers)
                
            status.update(label="Done!", state="complete")
        
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
                "FormDataObj_TransactionDocumentData_ReturnDate": "tanggal",
                "FormDataObj_TransactionDocumentData_ReturnDocumentNumber": "nota",
                "SellerTIN": "relasi",
                "kode": "kode",
                "qtybox": "qtybox",
                "qtylsn": "qtylsn",
                "FormDataObj_TransactionDetailsData_ReturnQuantity": "qtypcs",
                "hrgbox": "hrgbox",
                "hrglsn": "hrglsn",
                "FormDataObj_TransactionDetailsData_UnitPrice": "hrgpcs",
                "FormDataObj_TransactionDetailsData_ReturnDiscount": "discount",
                "FormDataObj_TransactionDetailsData_VATRate": "ppn",
                "FormDataObj_TransactionDocumentData_TaxInvoicePeriod": "sptmasa",
                "jmldpp": "jmldpp",
                "FormDataObj_TransactionDetailsData_ReturnVAT": "jmlppn",
                "SellerTaxpayerName": "nmsup",
                "FormDataObj_TransactionDetailsData_Name": "nmbrg",
                "divisi": "divisi",
                "FormDataObj_TransactionDocumentData_Reference": "ref"
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

                    sptmasa_value = base.get_period_end_date(period_code, year)

                    row = {
                        # pull in detail-level fields
                        # "FormDataObj_TransactionDetailsData_Type": d.get("Type", ""),
                        "FormDataObj_TransactionDetailsData_Name": d.get("Name", ""),
                        # "FormDataObj_TransactionDetailsData_Code": d.get("Code", ""),
                        "FormDataObj_TransactionDetailsData_ReturnQuantity": d.get("ReturnQuantity", 0),
                        # "FormDataObj_TransactionDetailsData_Unit": d.get("Unit", ""),
                        "FormDataObj_TransactionDetailsData_UnitPrice": d.get("UnitPrice", 0),
                        "FormDataObj_TransactionDetailsData_ReturnDiscount": d.get("ReturnDiscount", 0),
                        "FormDataObj_TransactionDetailsData_VATRate": d.get("VATRate", 0),
                        # "FormDataObj_TransactionDetailsData_ReturnTaxBase": d.get("ReturnTaxBase", 0),
                        "FormDataObj_TransactionDetailsData_ReturnVAT": d.get("ReturnVAT", 0),

                        # include parent-level info from FormDataObj_TransactionDocumentData
                        "FormDataObj_TransactionDocumentData_ReturnDate": payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("ReturnDate", ""),
                        "FormDataObj_TransactionDocumentData_ReturnDocumentNumber": payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("ReturnDocumentNumber", ""),
                        "FormDataObj_TransactionDocumentData_Reference": payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("Reference", ""),
                        "FormDataObj_TransactionDocumentData_TaxInvoicePeriod": sptmasa_value,

                        # add seller info
                        "SellerTIN": payload.get("SellerTIN", ""),
                        "SellerTaxpayerName": payload.get("SellerTaxpayerName", ""),
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
            df_all = df_all.loc[df_all["qtypcs"] > 0]
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
                file_name="coretax_input_return_details.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            status_placeholder.empty()
            st.error(f"Error: {e}")
    else:
        status_placeholder.empty()
        st.warning("No details were retrieved.")   
        
    

