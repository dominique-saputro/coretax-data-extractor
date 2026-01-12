import streamlit as st
import requests
import base64
import zlib
import json
from ast import literal_eval

st.set_page_config(
    page_title="Coretax Data Extractor",
    page_icon="📊",
)

st.write("# 📊 Coretax Data Extractor")

BASE_URL = "https://coretaxdjp.pajak.go.id"

query_params = st.query_params  # Streamlit ≥ 1.30 (modern API)


if "token" in st.session_state and st.session_state["token"]:
    token = st.session_state["token"]
    st.info("🔒 Using existing session token.")
else:
    # ------------ Use this for local testing
    # token = query_params.get("token", [None])[0] if isinstance(query_params.get("token"), list) else query_params.get("token")


    # ------------ Use this for production
    encoded = query_params.get("ct", [None])[0] if isinstance(query_params.get("ct"), list) else query_params.get("ct")
    token = None
    if encoded:
        try:
            # Convert URL-safe base64 → binary
            b64 = encoded.replace('-', '+').replace('_', '/')
            padded = b64 + '=' * (-len(b64) % 4)

            # Decode + decompress
            compressed = base64.b64decode(padded)
            decompressed = zlib.decompress(compressed)
            token_json = json.loads(decompressed.decode("utf-8"))
            token = token_json.get("access_token", [])

            st.success("✅ Token successfully decoded")
        except Exception as e:
            st.error(f"Failed to decode token: {e}")

if token:
    if "validated" not in st.session_state:
        status_placeholder = st.empty()
        status_placeholder.info("Validating token with Coretax API...")
        try:
            url = BASE_URL + "/identityproviderportal/connect/userinfo"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            taxpayer_id = data.get("taxpayer_id")
            taxpayer_name = data.get("full_name")
            tin = data.get("user_name")
            rep_tin = data.get("RepresentativeTin")
            roles = data.get("roles")
            roles = literal_eval(roles)
            roles = set(map(int, roles))
            
            # ------------ With Safety guard
            userid = [
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
                "0022978084651000", #DMS
                "0961882339624000", #DNX
                "0813485547806000", #DY
                "0023769375532000", #EMU
                "0022978076651000", #FWD
                "0012333423641000", #GB
                "0955176037605000", #LPL
                "00028245173614000", #MSA
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
                ]
            if tin in userid: 
                st.session_state["token"] = token
                st.session_state["taxpayer_id"] = taxpayer_id
                st.session_state["taxpayer_name"] = taxpayer_name
                st.session_state["rep_tin"] = rep_tin
                st.session_state["roles"] = roles
  
                st.session_state["allow_ppn"] = 32 in roles
                st.session_state["allow_unifikasi"] = 38 in roles
                st.session_state["allow_pph21"] = 42 in roles

                st.session_state["validated"] = True

                status_placeholder.empty()
                st.success(f"✅ Token Valid — Welcome {taxpayer_name or ''}")
                st.sidebar.success("Select a data extraction page above.")
            else:
                status_placeholder.empty()
                st.error(f"❌ Invalid — User {taxpayer_name or ''} not registered")
        except requests.exceptions.RequestException as e:
            status_placeholder.empty()
            st.error(f"Request failed: {e}")
    else:
        st.success(f"✅ Token active for {st.session_state.get('taxpayer_name', '')}")
        st.sidebar.success("Select a data extraction page above.")
else:
    st.warning("Please open this page with a valid token.")