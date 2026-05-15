import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="QuantEdge AI", layout="wide")

st.title("📈 QuantEdge AI - Stock Dashboard")

# Stock input
stock = st.text_input("Enter Stock Symbol (Example: RELIANCE.NS, TCS.NS)", "RELIANCE.NS")

# Fetch data
data = yf.download(stock, period="6mo")

if not data.empty:
    st.subheader("Stock Price Data")
    st.line_chart(data["Close"])

    st.subheader("Recent Data")
    st.dataframe(data.tail())
else:
    st.error("Invalid stock symbol!")
