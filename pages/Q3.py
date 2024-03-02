from pages.code.lib import *
import streamlit as st
import plotly.express as px
from statsmodels.tsa.statespace.structural import UnobservedComponents

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

data = get_forecast(data, filter_columns)

data["Filter"] = data[["Domain", "Element", "Item", "Unit"]].apply(lambda row: ' | '.join(row.values), axis=1)

selected_columns = data.drop(columns=["Year", "Value", "Unit", "Filter", "Area"]).columns

# Initialize a dictionary to store the selected values for each filter
selected_values = {column: 'All' for column in selected_columns}

columns = st.columns(len(selected_columns))

# Iterate over each column to create the selectboxes with dynamic options
for i, column in enumerate(selected_columns):
    # Filter the data based on the selections in other columns
    filtered_data = data
    for col, val in selected_values.items():
        if col != column and val != 'All':
            filtered_data = filtered_data[filtered_data[col] == val]

    # Determine the unique values for the current column in the filtered data
    unique_values = ['All'] + sorted(list(filtered_data[column].unique()))

    # Create the selectbox and update the selected value in the dictionary
    selected_value = columns[i].selectbox(f'Select {column}', options=unique_values, index=unique_values.index(selected_values[column]) if selected_values[column] in unique_values else 0)
    selected_values[column] = selected_value

# Apply filters to the data based on the final selections (if needed for further processing)
for column, selected_value in selected_values.items():
    if selected_value != 'All':
        data = data[data[column] == selected_value]

for idx, val in enumerate(data["Filter"].unique()):
    if idx > 5:
        break

    vis_data = data[data["Filter"] == val]
    # Create a color mapping for each country
    fig = px.line(vis_data, x = "Year", y ="Value", color = "Area", title = val, height=700)

    st.plotly_chart(fig, use_container_width = True)

