import streamlit as st
import requests
import base64
import zlib
import json

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

            st.session_state["taxpayer_id"] = taxpayer_id
            st.session_state["taxpayer_name"] = taxpayer_name
            st.session_state["validated"] = True

            status_placeholder.empty()
            st.success(f"✅ Token Valid — Welcome {taxpayer_name or ''}")
            st.sidebar.success("Select a data extraction page above.")
        except requests.exceptions.RequestException as e:
            status_placeholder.empty()
            st.error(f"Request failed: {e}")
    else:
        st.success(f"✅ Token active for {st.session_state.get('taxpayer_name', '')}")
        st.sidebar.success("Select a data extraction page above.")
else:
    st.warning("Please open this page with a valid token.")