import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from portfolio_backtester import (
    create_database_tables,
    get_portfolio_returns,
    get_benchmark_returns,
)

def start_app():
    create_database_tables()
    get_portfolio_returns()
    get_benchmark_returns()
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
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Drawdowns", "Returns", "Rolling Metrics"])
    with tab1:
        st.subheader("Portfolio Performance Summary")
        st.dataframe(summary_df[summary_df['Portfolio'].isin(selected_portfolios)], use_container_width=True)
        st.subheader("Portfolio Value Over Time")
        fig_value = go.Figure()
        for col in selected_portfolios:
            if "Benchmark" in col:
                fig_value.add_trace(go.Scatter(x=values.index, y=values[col], mode='lines', name=col, line=dict(dash='dash', color='black')))
            else:
                fig_value.add_trace(go.Scatter(x=values.index, y=values[col], mode='lines', name=col))
        fig_value.update_layout(yaxis_title="Portfolio Value ($)", xaxis_title="Date", template="plotly_white")
        st.plotly_chart(fig_value, use_container_width=True)
    with tab2:
        st.subheader("Portfolio Drawdowns Over Time")
        drawdowns = (values[selected_portfolios].cummax() - values[selected_portfolios]) / values[selected_portfolios].cummax()
        fig_dd = px.line(drawdowns, x=drawdowns.index, y=drawdowns.columns)
        fig_dd.update_layout(yaxis_title="Drawdown", xaxis_title="Date", template="plotly_white")
        st.plotly_chart(fig_dd, use_container_width=True)
    with tab3:
        st.subheader("Monthly Returns Distribution")
        monthly_returns = values[selected_portfolios].resample('M').last().pct_change().dropna()
        fig_hist = go.Figure()
        for col in monthly_returns.columns:
            fig_hist.add_trace(go.Histogram(x=monthly_returns[col], name=col, opacity=0.6, nbinsx=50))
        fig_hist.update_layout(barmode='overlay', xaxis_title="Return", yaxis_title="Frequency", template="plotly_white")
        st.plotly_chart(fig_hist, use_container_width=True)
    with tab4:
        st.subheader("Rolling Sharpe Ratio & Volatility")
        window = 63  
        fig_rm = go.Figure()
        for col in selected_portfolios:
            daily_returns = values[col].pct_change().dropna()
            rolling_sharpe = (daily_returns.rolling(window).mean() / daily_returns.rolling(window).std()) * np.sqrt(252)
            rolling_vol = daily_returns.rolling(window).std() * np.sqrt(252)
            fig_rm.add_trace(go.Scatter(x=rolling_sharpe.index, y=rolling_sharpe, mode='lines', name=f"{col} Sharpe"))
            fig_rm.add_trace(go.Scatter(x=rolling_vol.index, y=rolling_vol, mode='lines', name=f"{col} Volatility"))
        fig_rm.update_layout(yaxis_title="Metric Value", xaxis_title="Date", template="plotly_white")
        st.plotly_chart(fig_rm, use_container_width=True)
    with st.expander("View Transactions Table"):
        st.dataframe(transactions.sort_values(["date", "portfolio_name"]), use_container_width=True)

start_app()