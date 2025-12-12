import streamlit as st
import pandas as pd
import requests
import time
import datetime

BASE_URL = "https://coretaxdjp.pajak.go.id"
MAX_RETRIES = 3

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
    
    if not period_code:
        return ""
    try:
        base_date = month_end_map.get(period_code[:8], "")  # first 8 chars e.g. TD.00709
        if base_date and year:
            return f"{year}{base_date}"
        return base_date
    except Exception:
        return ""
    
def reverse_month_mapping(period):
    reverse_map = {v: k for k, v in month_mapping.items()}
    return reverse_map.get(period, "")
    
def auth_header(token,taxpayer_id,taxpayer_name):
    """
    Authorization layout for header
    """
    st.subheader(f"Authorization - {taxpayer_name}")
    if token and taxpayer_id:
        keepalive(token)
    else:
        if not token:
            st.warning("Token invalid.")
        if not taxpayer_id:
            st.warning("Taxpayer Id not found.")
    
def parameter_body(month_mapping=month_mapping):
    """
    Display default parameters for extractinng details.
    """
    st.subheader("Query Parameters")
    today = datetime.date.today()
    first_day_this_month = today.replace(day=1)
    last_month_last_day = first_day_this_month - datetime.timedelta(days=1)
    last_month_name = last_month_last_day.strftime("%B")

    # Prepare selectbox
    month_names = list(month_mapping.keys())
    default_index = month_names.index(last_month_name)
    months = st.selectbox(
        "Select month(s) for TaxInvoicePeriod",
        options=month_names,
        index=default_index,
    )
    period = month_mapping[months]
    year = st.number_input("TaxInvoiceYear", value=2025)
    rows = st.number_input("Number of Rows", min_value=100, max_value=10000, value=200, step=100)
    return period,year,rows

def fetch_details(status,details,fails,record_ids,token,taxpayer_id,url,headers):
    for i, rid in enumerate(record_ids):
        status.update(label=f"Fetching {i+1}/{len(record_ids)}...", state="running")
        if i % 500 == 0:
            keepalive(token)
            
        if "output" in url:
            payload = {
                "RecordIdentifier": f"{rid}",
                "EinvoiceVATStatus": "VAT_VAT",
                "TaxpayerAggregateIdentifier": f"{taxpayer_id}"
            }
        else:
            payload = {
                "RecordIdentifier": f"{rid}",
                "EinvoiceVATStatus": "",
                "TaxpayerAggregateIdentifier": f"{taxpayer_id}"
            }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=(10, 180))
            resp.raise_for_status()
            detail_data = resp.json()
            details.append(detail_data.get("Payload", detail_data))
        except requests.exceptions.RequestException as e:
            fails.append(rid)
            st.warning(f"⚠️ Failed to fetch details for RecordId[{i}]. Will try again later. Please Hold.")
        
    return details,fails