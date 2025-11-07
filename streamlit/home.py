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
st.markdown("""
<script>
window.addEventListener("message", (event) => {
  if (event.data && event.data.type === "CORETAX_TOKEN") {
    console.log("[Streamlit Bridge] 🪄 Received token:", event.data);
    const token = event.data.token?.access_token || event.data.token;
    if (token) {
      // Save token to localStorage for persistence
      localStorage.setItem("coretax_token", token);

      // Refresh the page with query param (small token-safe redirect)
      const newUrl = window.location.origin + window.location.pathname + "?token_ready=1";
      window.history.replaceState({}, "", newUrl);
      window.location.reload();
    }
  }
});
</script>
""", unsafe_allow_html=True)
# --- Read token if already stored ---
token = None
if "token" not in st.session_state:
    # Try recover from localStorage using Streamlit JS -> Python bridge
    st.markdown("""
    <script>
    const saved = localStorage.getItem("coretax_token");
    if (saved) {
        window.parent.postMessage({type: "streamlit_token_recover", token: saved}, "*");
    }
    </script>
    """, unsafe_allow_html=True)
else:
    token = st.session_state["token"]

# --- Listen for recovery ---
token_input = st.text_input("Debug Token (auto-filled)", value=token or "")
if token_input:
    st.session_state["token"] = token_input
    token = token_input

# query_params = st.query_params  # Streamlit ≥ 1.30 (modern API)
# token = query_params.get("token", [None])[0] if isinstance(query_params.get("token"), list) else query_params.get("token")

if token:
    # st.session_state["token"] = token
    status_placeholder = st.empty()
    status_placeholder.info("Validating token with Coretax API...")
    try:
        url = BASE_URL+"/identityproviderportal/connect/userinfo"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        st.write(headers)
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