import streamlit as st
import pandas as pd
import requests
import time
import datetime
import io
import zipfile
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://coretaxdjp.pajak.go.id"
MAX_RETRIES = 3
CHUNK_SIZE = 500        
MAX_WORKERS = 8        
REQUEST_TIMEOUT = (10, 120)

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

WHITELIST = [
    "0014826788619000", #AJP
    "0929849651606000", #ALAIKA
    "0011081726607000", #AMB
    "0017929589606000", #AP
    "0266437581619000", #APA
    "0613315589604000", #ASTA
    "0025326661714000", #BARTIM
    "0941727117424000", #BK
    "0827914995722000", #BKA
    "0017925165615000", #CM
    "0638937201609000", #CSP
    "0010001519052000", #DAI
    "0022978084651000", #DMS
    "0961882339624000", #DNX
    "0813485547806000", #DY
    "0023769375532000", #EMU
    "0022978076651000", #FWD
    "0012333423641000", #GB
    "0742752595619000", #KA4
    "0763620879604000", #LA
    "0029267960926000", #LM
    "0955176037605000", #LPL
    "0028245173614000", #MSA
    "0531867802606000", #ORC
    "0961899739925000", #PF
    "0712014273801000", #PLI
    "0022119804629000", #PMX
    "0031059744643000", #SAC
    "0621792662656000", #SIP
    "0011098050651000", #SKMS
    "0014815146614000", #SST
    "0530442896609000", #SYS
    "0025628108641000", #TMP
    "0769014697604000", #URD
    ##########################
    "3578210209810003", #YOHAN
    "3578092407720001", #ANTON
    "3578241110000001", #JASON
    "5101042704880003", #EKO
]

ROLE_SPT_MAPPING = {
    32: {
        "role": "PPN",
        "code": "VAT_VAT",
        "search_key":"-",
        "alt" : "PPN"
    },
    38: {
        "role": "Unifikasi",
        "code": "ICT_WT",
        "search_key":"Bukti Potong PPh Unifikasi (BPPU)",
        "alt" : "Unifikasi"
    },
    42: {
        "role": "PPh21",
        "code": "ICT_WIT",
        "search_key":"Bukti Potong PPh Pasal 21",
        "alt" : "A1 / BP21"
    }
}

def keepalive(token):
    """Ping the Coretax KeepAlive endpoint to maintain session"""
    url = BASE_URL + "/identityproviderportal/api/Account/SessionKeepAlive"
    headers = {
        "Accept":"application/json, text/plain, */*",
        "Connection": "keep-alive",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 OPR/128.0.0.0",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Referer":"https://coretaxdjp.pajak.go.id/registration-portal/id-ID/reg-home"
    }
    try:
        time.sleep(0.5)
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
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

def get_allowed_roles(code):
    order = [32, 38, 42]

    if not code:
        return {}

    # Ensure code is exactly 3 chars (pad if needed)
    code = str(code).zfill(3)

    allowed_roles = {}
    for digit, role in zip(code, order):
        if digit == "1":
            entry = ROLE_SPT_MAPPING[role]
            allowed_roles[entry["role"]] = entry

    return allowed_roles
    
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
    current_year = today.year

    # Prepare selectbox
    month_names = list(month_mapping.keys())
    default_index = month_names.index(last_month_name)
    months = st.selectbox(
        "Select month(s) for TaxInvoicePeriod",
        options=month_names,
        index=default_index,
    )
    period = month_mapping[months]
    year = st.number_input("TaxInvoiceYear", value=current_year)
    rows = st.number_input("Number of Rows", min_value=100, max_value=10000, value=200, step=100)
    return period,year,rows

def fetch_details(record_ids,token,taxpayer_id,url,headers):
    if "cursor" not in st.session_state:
        st.session_state.cursor = 0
        st.session_state.details = []
        st.session_state.fails = []

    total = len(record_ids)
    start = st.session_state.cursor
    end = min(start + CHUNK_SIZE, total)
    chunk = record_ids[start:end]

    with st.status(
        f"Processing records {start+1}–{end}/{total}",
        expanded=True
    ) as status:

        keepalive(token)

        details, fails = fetch_chunk_parallel(
            chunk,
            url,
            headers,
            token,
            taxpayer_id,
            status,
            MAX_WORKERS
        )

        st.session_state.details.extend(details)
        st.session_state.fails.extend(fails)
        st.session_state.cursor = end

        # 🔁 retry logic with cap
        retries = 0
        while st.session_state.fails and retries < MAX_RETRIES:
            retries += 1
            status.update(
                label=f"Retrying failed records ({retries}/{MAX_RETRIES})",
                state="running"
            )

            keepalive(token)

            retry_details, retry_fails = fetch_chunk_parallel(
                st.session_state.fails,
                url,
                headers,
                token,
                taxpayer_id,
                status,
                MAX_WORKERS
            )

            st.session_state.details.extend(retry_details)
            st.session_state.fails = retry_fails

        if st.session_state.cursor < total:
            st.warning(
                f"Fetched {st.session_state.cursor}/{len(record_ids)} records. "
                "Click 🔍 Fetch Data from Coretax again."
            )
            
        else:
            status.update(label="Done!", state="complete")
            st.success("🎉 All records fetched successfully!")

    return st.session_state.details

def fetch_one(rid, url, headers, token, taxpayer_id):
    if "output" in url:
        payload = {
            "RecordIdentifier": rid,
            "EinvoiceVATStatus": "VAT_VAT",
            "TaxpayerAggregateIdentifier": taxpayer_id
        }
    else:
        payload = {
            "RecordIdentifier": rid,
            "EinvoiceVATStatus": "",
            "TaxpayerAggregateIdentifier": taxpayer_id
        }

    resp = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=(10, 120)
    )
    resp.raise_for_status()
    return resp.json().get("Payload", {})

def fetch_chunk_parallel(
    record_ids,
    url,
    headers,
    token,
    taxpayer_id,
    status,
    max_workers=8
):
    results = []
    fails = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                fetch_one,
                rid,
                url,
                headers,
                token,
                taxpayer_id
            ): rid
            for rid in record_ids
        }

        for i, future in enumerate(as_completed(futures)):
            rid = futures[future]
            status.update(
                label=f"Fetched {i+1}/{len(record_ids)}",
                state="running"
            )

            try:
                results.append(future.result())
            except Exception:
                fails.append(rid)

    return results, fails

def build_zip_in_memory(responses):
    zip_buffer = io.BytesIO()
    total = len(responses)

    progress = st.progress(0)
    status = st.empty()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for i,r in enumerate(responses, start=1):
            status.info(f"Zipping {i}/{total}")
            pdf_bytes = base64.b64decode(r["Content"])
            filename = r.get("FileName", "file.pdf")
            zipf.writestr(filename, pdf_bytes)
            progress.progress(i / total)

    status.empty()
    progress.empty()

    zip_buffer.seek(0)
    return zip_buffer

