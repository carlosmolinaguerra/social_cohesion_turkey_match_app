import streamlit as st
import pandas as pd
import os
import io
import json
import requests
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

STOCK_FILE = "processed_file.xlsx"
LOG_FILE = "logs/submissions_log.jsonl"

st.title("Choose an option:")

option = st.radio("Choose an option:", ["Upload and Report", "Report Stock"])

# Ensure log directory exists
os.makedirs("logs", exist_ok=True)

def log_event(event_type, extra_info=None):
    # Get JS-side data (screen size, user agent)
    js_data = streamlit_js_eval(js_expressions=["window.innerWidth", "window.innerHeight", "navigator.userAgent"], key="jsdata")
    width, height, user_agent = js_data or [None, None, None]

    # IP-based info
    try:
        ip_info = requests.get("http://ip-api.com/json").json()
    except:
        ip_info = {}

    log_entry = {
        "timestamp_utc": datetime.utcnow().isoformat(),
        "event": event_type,
        "screen_width": width,
        "screen_height": height,
        "user_agent": user_agent,
        "ip_info": ip_info,
        "extra_info": extra_info or {}
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def process_file(df):
    expected_columns = {'n1', 'n2'}
    if set(df.columns) != expected_columns:
        raise ValueError("Excel file must contain exactly two columns: 'n1' and 'n2'")
    df['n1'] = df['n1'] / 2
    df['n2'] = df['n2'] / 3
    return df

if option == "Upload and Report":
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            processed_df = process_file(df)

            # Update stock
            if os.path.exists(STOCK_FILE):
                df_stock = pd.read_excel(STOCK_FILE)
                df_stock = pd.concat([df_stock, processed_df], ignore_index=True)
            else:
                df_stock = processed_df
            df_stock.to_excel(STOCK_FILE, index=False)

            st.success("File processed and stock updated!")
            st.dataframe(processed_df)

            # Log upload
            log_event("file_uploaded", {"uploaded_rows": len(df)})

            # Download button
            buffer = io.BytesIO()
            processed_df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                label="Download processed file",
                data=buffer,
                file_name="processed_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Error: {e}")

elif option == "Report Stock":
    if os.path.exists(STOCK_FILE):
        df_stock = pd.read_excel(STOCK_FILE)
        st.write("Current stock:")
        st.dataframe(df_stock)

        # Log download
        log_event("stock_downloaded", {"rows": len(df_stock)})

        buffer = io.BytesIO()
        df_stock.to_excel(buffer, index=False)
        buffer.seek(0)
        st.download_button(
            label="Download stock file",
            data=buffer,
            file_name="stock_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No stock file found. Please upload a file first using the other option.")