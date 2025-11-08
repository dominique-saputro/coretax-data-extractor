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
token = query_params.get("token", [None])[0] if isinstance(query_params.get("token"), list) else query_params.get("token")
# encoded = query_params.get("ct", [None])[0] if isinstance(query_params.get("ct"), list) else query_params.get("ct")

# token = None
# if encoded:
#     try:
#         # Convert URL-safe base64 → binary
#         b64 = encoded.replace('-', '+').replace('_', '/')
#         padded = b64 + '=' * (-len(b64) % 4)

#         # Decode + decompress
#         compressed = base64.b64decode(padded)
#         decompressed = zlib.decompress(compressed)
#         token_json = json.loads(decompressed.decode("utf-8"))
#         token = token_json.get("access_token", [])

#         st.success("✅ Token successfully decoded")
#     except Exception as e:
#         st.error(f"Failed to decode token: {e}")

if token:
    # st.write(token)
    st.session_state["token"] = token
    status_placeholder = st.empty()
    status_placeholder.info("Validating token with Coretax API...")
    try:
        url = BASE_URL+"/identityproviderportal/connect/userinfo"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract data items
        # df = pd.json_normalize(data.get("Items", data))
        # st.dataframe(df)
        
        taxpayer_id = data.get("taxpayer_id")
        # st.write(taxpayer_id)
        
        st.session_state["taxpayer_id"] = taxpayer_id
        status_placeholder.empty()
        st.success("✅ Token Valid")
        st.sidebar.success("Select a extraction data above.")
    except requests.exceptions.RequestException as e:
        status_placeholder.empty()
        st.error(f"Request failed: {e}")
else:
    st.warning("No token provided in the URL.")