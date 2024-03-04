
import os
import re
import json
import json_repair
import pytesseract

from PIL import Image
from hugchat import hugchat
from hugchat.login import Login
from pages.code.login import Login
#from login import Login

import pandas as pd
import streamlit as st

from pdf2image import convert_from_path, convert_from_bytes
import pandas as pd
from ydata_profiling import ProfileReport, compare
import streamlit as st


from streamlit_ydata_profiling import st_profile_report

import base64


# Function to convert image to Base64
def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Embed the Base64 encoded image and title in HTML with larger text size
def get_image_html(base64_string, width=300, height=300, title="Coco Cafe", font_size="48px"):
    return f'''
    <div style="text-align: center;">
        <img src="data:image/png;base64,{base64_string}" width="{width}" height="{height}" style="margin: 0 auto;">
        <h1 style="margin: 10px 0 0 0; font-size: {font_size};">{title}</p>
    </div>
    '''

@st.cache_data(show_spinner = "Loading Data")
def get_data():
    return dict(land_data = pd.read_csv("data/land.csv"),
                production_data = pd.read_csv("data/production.csv"),
                trade_data = pd.read_csv("data/trade.csv",),) # This could be more automated

@st.cache_data(show_spinner = "Loading Raw Data Report", experimental_allow_widgets=True)
def get_raw_report():
    data = get_data()
    kwargs = dict(samples=None, correlations=None, missing_diagrams=None, duplicates=None, interactions=None)
    return st_profile_report(compare([ProfileReport(val, title = key.replace("_", " ").capitalize(), **kwargs)for key, val in data.items()]))

@st.cache_data(show_spinner = "Cleaning Data")
def clean_data(data, 
               remove_columns: list[str] = ["Domain Code", "Area Code (M49)", "Element Code", "Item Code (CPC)", "Flag", "Year Code", "Note"], 
               na_subset: list[str] = ["Unit", "Value", "Flag Description"]):

    land_remove_columns = ["Domain Code", "Area Code (M49)", "Element Code", "Item Code", "Flag", "Year Code", "Note"]

    cleaned_data = {}
    for key, val in data.items():
        if key == "land_data":
            cleaned_val = val.drop(columns=land_remove_columns)
            cleaned_val = cleaned_val.dropna(subset=na_subset, axis=0)
        else:
            cleaned_val = val.drop(columns=remove_columns)
            cleaned_val = cleaned_val.dropna(subset=na_subset, axis=0)
        cleaned_data[key] = cleaned_val

    return cleaned_data

@st.cache_data(show_spinner = "Loading Clean Data Report", experimental_allow_widgets=True)
def get_clean_report():
    data = get_data()
    kwargs = dict(samples=None, correlations=None, missing_diagrams=None, duplicates=None, interactions=None)
    data = clean_data(data)
    return st_profile_report(compare([ProfileReport(val, title = key.replace("_", " ").capitalize(), **kwargs)for key, val in data.items()]))

@st.cache_data(show_spinner = "Joining Data")
def join_data(data):
    return pd.concat([val for _, val in data.items()])

@st.cache_data(show_spinner = "OCR Text Extraction")
def extract_ocr_text(file_path: str, file_content = None, file_type: str ='image'):
    ocr_text = ""
    if file_type == 'image':
        image = Image.open(file_path if file_path else file_content)
        st.image(image, caption='Image', use_column_width=True)
        ocr_text += "\n" + pytesseract.image_to_string(image)
    elif file_type == 'pdf':
        pages = convert_from_path(file_path) if file_path else convert_from_bytes(file_content)
        for idx, page in enumerate(pages):
            if idx == 0:
                st.image(page, caption='Uploaded Image', use_column_width=True)
            ocr_text += "\n" + pytesseract.image_to_string(page)
            if idx > 5:
                break
    return ocr_text

def get_invoice_files(invoices_dir: str, allowed_file_types: list):
    return [os.path.join(invoices_dir, f) for f in os.listdir(invoices_dir) if any(f.endswith(ext) for ext in allowed_file_types)]



@st.cache_data(show_spinner = "Generating Prompt")
def generate_prompt(ocr_extracted_text: str, json_structure: dict):
    prompt = f"""
Task: Provide a structured JSON given the text below

Text:

{ocr_extracted_text}
"""
    return prompt

@st.cache_data(show_spinner = "LLM JSON Generation")
def query_llm(prompt: str, model: str, email: str = "EMAIL", password: str = "PASSWORD"):
    
    #sign = Login(st.secrets[email], st.secrets[password])
    sign = Login(email, password)
    
    cookies = sign.login(save_cookies=False)
    chatbot = hugchat.ChatBot(cookies=cookies.get_dict(),) 
    llm_list = {llm.name:idx for idx, llm in enumerate(chatbot.get_available_llm_models())}
    chatbot.switch_llm(llm_list[model])

    attempts = {}

    # Initialize is_retry flag
    is_retry = False

    for attempt in range(5):

        llm_extracted_text = []
        for idx, response in enumerate(chatbot.query(prompt,use_cache=True, truncate=10000000, max_new_tokens=100000000, return_full_text=True, stream=True, is_retry=is_retry)):
            try:
                llm_extracted_text.append(response["token"])
            except:
                pass

        llm_extracted_text = "{Response: " + "".join(llm_extracted_text) + " }"

        json_text = json_repair.repair_json(llm_extracted_text, return_objects=True)

        attempts[f"Attempt {attempt + 1}"] = json_text

        if attempt == 0:
            is_retry = True

    return attempts


@st.cache_data(show_spinner = "Generating Forecast")
def get_forecast(data, filter_columns, steps = 5):
    forecast_df = data[["Year", "Value", "Filter"]].pivot_table(index = "Year", columns="Filter", values="Value", aggfunc="mean")
    forecast_df = forecast_df.reindex(range(forecast_df.index.min(), forecast_df.index.max() + steps + 1))
    forecast_df  = forecast_df.interpolate(mmethod='akima', axis="index", limit_direction = "both")
    forecast_df = forecast_df.reset_index().melt(id_vars="Year")
    forecast_df = forecast_df.merge(pd.DataFrame([dict(zip(filter_columns, values)) for values in forecast_df["Filter"].str.split("|").to_list()]), left_index=True, right_index=True).rename(columns={"value":"Value"})
    return forecast_df