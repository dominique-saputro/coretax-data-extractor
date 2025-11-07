import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import io
import time

st.set_page_config(
    page_title="Coretax Data Extractor",
    page_icon="📊",
)

st.write("# 📊 Coretax Data Extractor")

BASE_URL = "https://coretaxdjp.pajak.go.id"

# Placeholder to hold token
token = components.html(
    """
    <script>
    const doc = window.parent.document;
    // Listen for postMessage from extension background
    window.addEventListener("message", (event) => {
      if (event.data && event.data.type === "SET_TOKEN") {
        const token = event.data.token?.access_token || event.data.token;
        console.log("📥 Received token via postMessage:", token);

        // Notify Streamlit backend
        const streamlitEvent = new CustomEvent("streamlit:setComponentValue", { detail: token });
        doc.dispatchEvent(streamlitEvent);
      }
    });
    </script>
    """,
    height=0,
)

# query_params = st.query_params  # Streamlit ≥ 1.30 (modern API)
# token = query_params.get("token", [None])[0] if isinstance(query_params.get("token"), list) else query_params.get("token")

if token:
    st.write(st.session_state["token"])
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
    st.warning("No token received yet. Please capture it via the extension.")