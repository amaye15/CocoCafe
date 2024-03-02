import os
import streamlit as st
from pages.code.lib import *

st.set_page_config(layout="wide")

###################################################
# Section - Constants
###################################################

# Supporting both images and PDFs
ALLOWED_IMAGE_TYPES = ["jpeg", "jpg", "png"]
ALLOWED_FILE_TYPES = ALLOWED_IMAGE_TYPES + ["pdf"]
MODEL = "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO"
JSON_FORMATTER = 'format.json'
INVOICE_PATH = './documents'

st.title('Invoice Viewer')

# Create two columns
col1, col2 = st.columns(2)

###################################################
# Section - Select/ Upload File
###################################################

# Upload an image or PDF
uploaded_file = st.file_uploader("Choose an image or PDF file...", type=ALLOWED_FILE_TYPES)

# Select an image or PDF from the directory
if uploaded_file is None:
    invoice_files = get_invoice_files(INVOICE_PATH, ALLOWED_FILE_TYPES)
    selected_file = st.selectbox('Or choose a pre-existing invoice file:', invoice_files, format_func=lambda x: os.path.basename(x))
else:
    selected_file = None

# Display the uploaded or selected file
if uploaded_file is not None:
    file_type = 'image' if any(uploaded_file.name.endswith(ext) for ext in ALLOWED_IMAGE_TYPES) else 'pdf'
    ocr_extracted_text = extract_ocr_text(None, uploaded_file, file_type)
elif selected_file:
    file_type = 'image' if any(selected_file.endswith(ext) for ext in ALLOWED_IMAGE_TYPES) else 'pdf'
    ocr_extracted_text = extract_ocr_text(selected_file, None, file_type)

json_structure = {} #load_data(JSON_FORMATTER)

# Generate the prompt using the cached function
prompt = generate_prompt(ocr_extracted_text, json_structure)

llm_extracted_text = query_llm(prompt = prompt, model = MODEL, email = st.secrets["email"], password = st.secrets["password"])

#json_text = json_repair.repair_json(llm_extracted_text, return_objects=True)

for key, val in llm_extracted_text.items():
    st.subheader(key)
    st.json(val)