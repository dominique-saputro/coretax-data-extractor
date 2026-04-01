import streamlit as st
import socket

try:
    ip = socket.gethostbyname("coretaxdjp.pajak.go.id")
    st.write(f"Resolved IP: {ip}")
except Exception as e:
    st.write(f"DNS failed: {e}")