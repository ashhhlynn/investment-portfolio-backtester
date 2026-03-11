import streamlit as st
import pandas as pd
import sqlite3
import numpy as np

conn = sqlite3.connect("portfolio.db")
values = pd.read_sql("SELECT * FROM portfolio_values", conn)
values['date'] = pd.to_datetime(values['date'])
values = values.pivot(index='date', columns='portfolio_name', values='portfolio_value')
transactions = pd.read_sql("SELECT * FROM transactions", conn)
transactions['date'] = pd.to_datetime(transactions['date'])
summary = []
for portfolio_name in values.columns:
    series = values[portfolio_name].dropna()
    years = (series.index[-1] - series.index[0]).days / 365.25
    start_value = series.iloc[0]
    end_value = series.iloc[-1]
    cagr = (end_value / start_value)**(1/years) - 1
    daily_returns = series.pct_change().dropna()
    vol = daily_returns.std() * np.sqrt(252)
    sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
    rolling_max = series.cummax()
    drawdown = (series - rolling_max) / rolling_max
    max_dd = drawdown.min()
    summary.append({
        "Portfolio": portfolio_name,
        "CAGR": cagr,
        "Volatility": vol,
        "Sharpe": sharpe,
        "Max Drawdown": max_dd
    })
summary_df = pd.DataFrame(summary)
summary_df['CAGR'] = summary_df['CAGR'].map("{:.2%}".format)
summary_df['Volatility'] = summary_df['Volatility'].map("{:.2%}".format)
summary_df['Max Drawdown'] = summary_df['Max Drawdown'].map("{:.2%}".format)
summary_df['Sharpe'] = summary_df['Sharpe'].map("{:.2f}".format)
st.set_page_config(page_title="Portfolio Backtest Dashboard", layout="wide")
st.title("📊 Portfolio Backtester Dashboard")
portfolio_list = values.columns.tolist()
selected_portfolios = st.multiselect("Select portfolios to analyze:", portfolio_list, default=portfolio_list)

with st.expander("View Transactions Table"):
    st.dataframe(transactions.sort_values(["date", "portfolio_name"]), use_container_width=True)