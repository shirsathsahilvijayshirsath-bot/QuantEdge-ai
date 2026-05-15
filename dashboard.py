import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="QuantEdge AI", layout="wide")

st.title("📈 QuantEdge AI - Advanced Stock Dashboard")

# Sidebar
st.sidebar.header("Settings")

stock = st.sidebar.text_input("Stock Symbol", "RELIANCE.NS")

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# Validation
if stock == "":
    st.warning("Please enter a stock symbol")
    st.stop()

# Fetch data
data = yf.download(stock, start=start_date, end=end_date)

if data.empty:
    st.error("Invalid stock symbol or no data found")
    st.stop()

# Moving averages
data["50_MA"] = data["Close"].rolling(window=50).mean()
data["200_MA"] = data["Close"].rolling(window=200).mean()

# Layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Price Chart")
    st.line_chart(data[["Close", "50_MA", "200_MA"]])

with col2:
    st.subheader("📋 Recent Data")
    st.dataframe(data.tail())

# Extra info
st.subheader("📈 Key Stats")

st.write("Latest Price:", round(data["Close"].iloc[-1], 2))
st.write("Highest Price:", round(data["High"].max(), 2))
st.write("Lowest Price:", round(data["Low"].min(), 2))
