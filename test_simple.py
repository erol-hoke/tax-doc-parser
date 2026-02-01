import streamlit as st

st.set_page_config(page_title="Tax Parser", layout="wide")
st.title("📄 Tax Document Parser")
st.write("If you see this, the app is working!")

uploaded = st.file_uploader("Upload a test file", type=['pdf', 'png'])
if uploaded:
    st.success(f"Uploaded: {uploaded.name}")
