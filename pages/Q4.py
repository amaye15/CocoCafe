from pages.code.lib import *
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")

image_path = 'logo.png'
image_base64 = get_image_base64(image_path)
html_content = get_image_html(image_base64)

st.markdown(html_content, unsafe_allow_html=True)

filter_columns = ["Domain", "Area", "Element", "Item", "Unit"]

data = get_data()
data = clean_data(data)
data = join_data(data)
data["Filter"] = data[filter_columns].apply(lambda row: ' | '.join(row.values), axis=1)

selected_columns = data.drop(columns=["Year", "Value", "Unit", "Filter", "Area", "Flag Description"]).columns

data = get_forecast(data, filter_columns)
df = data[(data['Item'].str.contains('cocoa|chocolate', case=False, na=False)) & (data['Filter'].str.contains('export value', case=False, na=False))]

df.loc[(df['Item'].str.contains('cocoa beans', case=False, na=False)), "Value"] = df.loc[(df['Item'].str.contains('cocoa beans', case=False, na=False)), "Value"] * (1 - 0.3)
df.loc[(~df['Item'].str.contains('cocoa beans', case=False, na=False)), "Value"] = df.loc[(~df['Item'].str.contains('cocoa beans', case=False, na=False)), "Value"] * (1 - 0.02)
df.loc[(~df['Item'].str.contains('cocoa beans', case=False, na=False)), "Item"] = "Cocao Product"

tmp = df.drop(columns="Filter").groupby(by = ["Domain", "Area", "Element", "Item", "Year", "Unit"]).sum().reset_index()

for area in tmp["Area"].unique():
    tmp2 = tmp[tmp["Area"] == area]


    fig = px.bar(tmp2, x = "Year", y = "Value", color = "Item", title = f"{area} - Export Value After Tax", barmode='group')

    st.plotly_chart(fig, use_container_width = True)