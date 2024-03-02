

from pages.code.lib import get_image_base64, get_image_html, get_raw_report, get_clean_report
import streamlit as st


st.set_page_config(layout="wide")


image_path = 'logo.png'
image_base64 = get_image_base64(image_path)
html_content = get_image_html(image_base64)

st.markdown(html_content, unsafe_allow_html=True)

# Create two columns
col1, col2 = st.columns(2)

with col1:
    get_raw_report()

with col2:
    get_clean_report()