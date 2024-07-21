import streamlit as st
import pandas as pd
import re
import os
from dateutil import parser

# Function to clean and format dates
def format_date(date_str):
    if pd.isna(date_str):
        return None
    try:
        # Handle specific format '2024 05 (May '24)'
        match = re.match(r'(\d{4}) (\d{2}) \(\w+ \'\d{2}\)', date_str)
        if match:
            year, month = match.groups()
            date = f"{year}-{month}-01"
            return pd.to_datetime(date, format='%Y-%m-%d').strftime('%d-%m-%Y')

        # Use dateutil.parser to handle other date formats
        date = parser.parse(date_str, fuzzy=True)
        return date.strftime('%d-%m-%Y')
    except Exception as e:
        st.error(f"Error parsing date: {date_str} -> {e}")
        return None

def process_file(file, sheet_name=None, date_col='Month', group_cols=None, sum_cols=None, agg_func='sum', date_format_func=format_date):
    # Check file extension to determine reading method
    if file.name.endswith('.xlsx'):
        # Load the data from the specified sheet in Excel file
        data = pd.read_excel(file, sheet_name=sheet_name)
    elif file.name.endswith('.csv'):
        # Load the data from the CSV file
        data = pd.read_csv(file)
    else:
        st.error("Unsupported file type. Please provide a .xlsx or .csv file.")
        return None

    # List available columns
    available_columns = data.columns.tolist()
    st.write("Available columns in the uploaded file:", available_columns)

    # Drop any completely empty rows
    data.dropna(how='all', inplace=True)

    # Apply the date formatting function
    data['Formatted Month'] = data[date_col].apply(date_format_func)

    # Drop rows with invalid dates
    data = data.dropna(subset=['Formatted Month'])

    # Check for missing columns
    if sum_cols:
        missing_cols = [col for col in sum_cols if col not in data.columns]
        if missing_cols:
            st.error(f"Missing columns: {missing_cols}")
            return None

        # Convert columns to sum to numeric, errors='coerce' will turn non-convertible values to NaN
        data[sum_cols] = data[sum_cols].apply(pd.to_numeric, errors='coerce')

        # Group by formatted month and specified columns, then aggregate the relevant columns
        if agg_func == 'sum':
            aggregated_data = data.groupby(['Formatted Month'] + group_cols)[sum_cols].sum().reset_index()
        elif agg_func == 'mean':
            aggregated_data = data.groupby(['Formatted Month'] + group_cols)[sum_cols].mean().reset_index()
        elif agg_func == 'median':
            aggregated_data = data.groupby(['Formatted Month'] + group_cols)[sum_cols].median().reset_index()
        else:
            st.error("Unsupported aggregation function")
            return None

        # Save the cleaned and aggregated data to a new CSV file
        output_file_path = 'Cleaned_Aggregated_Data.csv'
        aggregated_data.to_csv(output_file_path, index=False)

        st.success("Data processed successfully!")
        st.download_button(
            label="Download Cleaned Data",
            data=aggregated_data.to_csv(index=False),
            file_name=output_file_path,
            mime='text/csv',
        )

        return aggregated_data
    else:
        st.error("No columns selected for summing")
        return None

st.title("Jackson's Data Aggregation Tool")
st.write("Upload an Excel or CSV file to clean and aggregate data.")

# File uploader
uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'csv'])

if uploaded_file is not None:
    # Display a preview of the uploaded file
    if uploaded_file.name.endswith('.xlsx'):
        sheet_names = pd.ExcelFile(uploaded_file).sheet_names
        sheet_name = st.selectbox("Select sheet", sheet_names)
        if sheet_name:
            data = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    elif uploaded_file.name.endswith('.csv'):
        data = pd.read_csv(uploaded_file)
    
    if data is not None:
        st.write("Preview of the uploaded data:")
        st.write(data.head())

        available_columns = data.columns.tolist()
        st.write("Available columns in the uploaded file:", available_columns)

        date_col = st.selectbox("Select the date column", available_columns)
        group_cols = st.multiselect("Select columns to group by", available_columns)
        sum_cols = st.multiselect("Select columns to sum", available_columns)
        agg_func = st.selectbox("Select aggregation function", ['sum', 'mean', 'median'])

        if st.button("Process File"):
            with st.spinner('Processing...'):
                result = process_file(uploaded_file, sheet_name=sheet_name if uploaded_file.name.endswith('.xlsx') else None, date_col=date_col, group_cols=group_cols, sum_cols=sum_cols, agg_func=agg_func)
                if result is not None:
                    st.write("Aggregated Data:")
                    st.write(result)
                    st.line_chart(result.set_index('Formatted Month')[sum_cols])  # Example visualization

