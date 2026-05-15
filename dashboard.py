import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="QuantEdge AI", layout="wide")

st.title("📈 QuantEdge AI - Stock Dashboard")

# Stock input
stock = st.text_input("Enter Stock Symbol (Example: RELIANCE.NS, TCS.NS)")

# Empty check
if stock == "":
    st.warning("Please enter a stock symbol")
    st.stop()

# Fetch data
data = yf.download(stock, period="6mo")

# Data check
if data.empty:
    st.error("Invalid stock symbol or no data found")
    st.stop()

# Show data
st.subheader("Stock Price Data")
st.line_chart(data["Close"])

st.subheader("Recent Data")
st.dataframe(data.tail())
