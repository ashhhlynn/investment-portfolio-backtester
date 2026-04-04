import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.graph_objects as go
from portfolio_backtester import (
    create_database_tables,
    get_portfolio_returns,
    get_benchmark_returns,
)

@st.cache_data
def get_data():
    create_database_tables()    
    get_portfolio_returns()
    get_benchmark_returns()
    conn = sqlite3.connect("portfolio.db")
    values = pd.read_sql("SELECT * FROM portfolio_values", conn)
    values['date'] = pd.to_datetime(values['date'])
    transactions = pd.read_sql("SELECT * FROM transactions", conn)
    transactions['date'] = pd.to_datetime(transactions['date'])
    return values, transactions

def start_app():
    values, transactions = get_data()
    values = values.pivot(index='date', columns='portfolio_name', values='portfolio_value')
    summary_df = get_calculations_summary(values)
    st.set_page_config(page_title="Portfolio Backtest Dashboard", layout="wide")
    st.title("Portfolio Backtester")
    portfolio_list = values.columns.tolist() 
    portfolio_list.append(portfolio_list.pop(portfolio_list.index('SPY Benchmark')))
    selected_portfolios = st.multiselect("Select portfolios to analyze:", portfolio_list, default=portfolio_list)
    tab1, tab2, tab3, tab4, tab5= st.tabs(["Overview", "Risk vs. Return", "Annual Returns", "Drawdowns", "Rolling Sharpe"])
    with tab1: 
        st.subheader("Portfolio Performance Summary")
        get_summary_chart(selected_portfolios, summary_df)
        st.subheader("Portfolio Value Over Time")
        get_values_chart(selected_portfolios, values)
    with tab2:
        st.subheader("Portfolio Risk vs. Return")
        get_risk_returns_chart(selected_portfolios, summary_df)
    with tab3:
        st.subheader("Portfolio Annual Returns")
        get_annual_returns_chart(selected_portfolios, values)
    with tab4:
        st.subheader("Portfolio Drawdowns Over Time")    
        get_drawdowns_chart(selected_portfolios, values)
    with tab5:
        st.subheader("Portfolio Rolling Sharpe Ratio")
        get_rolling_charts(selected_portfolios, values)
    get_recent_transactions(transactions)

def get_calculations_summary(values):
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
    summary_df = pd.DataFrame(summary).sort_values(["CAGR"])
    summary_df['CAGR'] = summary_df['CAGR'].map("{:.2%}".format)
    summary_df['Volatility'] = summary_df['Volatility'].map("{:.2%}".format)
    summary_df['Max Drawdown'] = summary_df['Max Drawdown'].map("{:.2%}".format)
    summary_df['Sharpe'] = summary_df['Sharpe'].map("{:.2f}".format)
    return summary_df

def get_summary_chart(selected_portfolios, summary_df):
    mask = summary_df['Portfolio'].isin(selected_portfolios)
    filtered_df = summary_df[mask]
    filtered_df['CAGR'] = pd.to_numeric(filtered_df['CAGR'].str.replace('%', '', regex=False))
    filtered_df['Volatility'] = pd.to_numeric(filtered_df['Volatility'].str.replace('%', '', regex=False))  
    filtered_df['Max Drawdown'] = pd.to_numeric(filtered_df['Max Drawdown'].str.replace('%', '', regex=False))  
    styled_df = filtered_df.style.background_gradient(
        subset=['Max Drawdown', 'CAGR', 'Sharpe'], 
        cmap='GnBu', 
        low=-.6, 
        high=.2
    ).background_gradient(
        subset=['Volatility'], 
        cmap='GnBu_r', 
        low=.5, 
        high=.1
    ).format(
        "{:.2f}%", 
        subset=['CAGR', 'Volatility', 'Max Drawdown']
    )
    st.dataframe(
        styled_df, 
        use_container_width=True, 
        hide_index=True, 
        column_config={"Sharpe": {"alignment": "right"}}
    )   

def get_values_chart(selected_portfolios, values):
    fig_value = go.Figure()
    for col in selected_portfolios:
        if "Benchmark" in col:
            fig_value.add_trace(go.Scattergl(
                x=values.index, 
                y=values[col], 
                mode='lines', 
                name=col, 
                line=dict(color='navy')
            ))
        else:
            fig_value.add_trace(go.Scattergl(
                x=values.index, 
                y=values[col], 
                mode='lines', 
                name=col
            ))
    fig_value.update_layout(
        yaxis_title="Portfolio Value ($)", 
        xaxis_title="Date", 
        legend_title="Portfolio", 
        hovermode="x unified", 
        xaxis_rangeslider_visible=False, 
        template="plotly_white"
    )
    st.plotly_chart(fig_value, use_container_width=True)

def get_risk_returns_chart(selected_portfolios, summary_df):
    fig_rr = go.Figure()
    summary_df_copy = summary_df.copy()
    summary_df_copy['CAGR'] = pd.to_numeric(summary_df_copy['CAGR'].str.replace('%', '', regex=False))
    summary_df_copy['Volatility'] = pd.to_numeric(summary_df_copy['Volatility'].str.replace('%', '', regex=False))        
    for col in selected_portfolios:
        cagr_value = summary_df_copy.loc[summary_df_copy['Portfolio'] == col, 'CAGR'].values[0]
        vol_value = summary_df_copy.loc[summary_df_copy['Portfolio'] == col, 'Volatility'].values[0]
        sharpe_value = (float(summary_df_copy.loc[summary_df_copy['Portfolio'] == col, 'Sharpe'].values[0]))
        if "Benchmark" in col:
            fig_rr.add_trace(go.Scatter(
                x=[vol_value], 
                y=[cagr_value], 
                mode='markers+text', 
                name=col, 
                textposition="bottom left", 
                text=col, 
                marker=dict(color='navy', size=(sharpe_value**2)*50),
                hovertemplate=
                f"{col}<br>" +
                "CAGR: %{y:.2f}%<br>" +
                "Volatility: %{x:.2f}%<br>" +
                f"Sharpe: {sharpe_value:.2f}" +
                "<extra></extra>"
            ))
        else:
            fig_rr.add_trace(go.Scatter(
                x=[vol_value], 
                y=[cagr_value], 
                mode='markers+text', 
                name=col, 
                textposition="bottom left", 
                text=col,
                marker=dict(size=(sharpe_value**2)*50),
                hovertemplate=
                f"{col}<br>" +
                "CAGR: %{y:.2f}%<br>" +
                "Volatility: %{x:.2f}%<br>" +
                f"Sharpe: {sharpe_value:.2f}" +
                "<extra></extra>"
            ))
    fig_rr.update_layout(
        xaxis=dict(title='Volatility (%)'),
        yaxis=dict(title='CAGR (%)'),
        showlegend=False,
        template='plotly_white'
    )
    fig_rr.update_yaxes(scaleanchor="x", scaleratio=1) 
    st.plotly_chart(fig_rr, use_container_width=True)

def get_annual_returns_chart(selected_portfolios, values):
    annual_prices = values.resample('YE').last()
    first_day = values.iloc[:1]
    combined_data = pd.concat([first_day, annual_prices])
    annual_returns = combined_data.pct_change().dropna()
    annual_returns_df = pd.DataFrame(annual_returns).T
    annual_returns_df.columns = pd.to_datetime(annual_returns_df.columns).year
    annual_returns_df.index.name = 'Portfolio'
    mask = annual_returns_df.index.isin(selected_portfolios)
    filtered_df = annual_returns_df[mask]
    styled_table = filtered_df.style.background_gradient(
        cmap='GnBu', 
        vmin=-.20, 
        vmax=0.60, 
        low=.2
    ).format("{:.2%}")
    st.dataframe(styled_table, use_container_width=True)

def get_drawdowns_chart(selected_portfolios, values):
    drawdowns = values[selected_portfolios] / values[selected_portfolios].cummax() - 1    
    fig_dd = go.Figure()
    for col in selected_portfolios:
        trace_type = go.Scattergl         
        if "Benchmark" in col:
            fig_dd.add_trace(trace_type(
                x=drawdowns.index, 
                y=drawdowns[col], 
                mode='lines', 
                name=col, 
                line=dict(color='navy')
            ))
        else:
            fig_dd.add_trace(trace_type(
                x=drawdowns.index, 
                y=drawdowns[col], 
                mode='lines', 
                name=col
            ))
    fig_dd.update_layout(
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        legend_title="Portfolio",
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        template="plotly_white"
    )
    fig_dd.update_yaxes(
        tickformat=".2%",     
        range=[None, 0]    
    )
    st.plotly_chart(fig_dd, use_container_width=True)

def get_rolling_charts(selected_portfolios, values):
    window = 252
    fig_rm = go.Figure()
    for col in selected_portfolios:
        daily_returns = values[col].pct_change().dropna()
        rolling_sharpe = (daily_returns.rolling(window).mean() / daily_returns.rolling(window).std()) * np.sqrt(252)
        if "Benchmark" in col:
            fig_rm.add_trace(go.Scattergl(
                x=rolling_sharpe.index, 
                y=rolling_sharpe, 
                mode='lines', 
                name=col, 
                line=dict(color='navy')
            ))
        else:
            fig_rm.add_trace(go.Scattergl(
                x=rolling_sharpe.index, 
                y=rolling_sharpe, 
                mode='lines', 
                name=col
            ))
    fig_rm.add_hline(y=0, line_dash="dot", opacity=0.6)
    fig_rm.add_hline(y=1, line_dash="dot", opacity=0.6)
    fig_rm.update_layout(
        yaxis_title="Sharpe Ratio", 
        xaxis_title="Date", 
        legend_title="Portfolio",
        hovermode="x unified", 
        xaxis_rangeslider_visible=False,
        template="plotly_white"
    ) 
    fig_rm.update_yaxes(
        tickformat=".2f"
    )
    st.plotly_chart(fig_rm, use_container_width=True)

def get_recent_transactions(transactions):
    recent = transactions.sort_values(["date"]).tail(20)
    recent.columns = recent.columns.str.replace('_', ' ').str.title()
    recent['Date'] = recent['Date'].dt.date
    recent['Action'] = recent['Action'].str.title()
    with st.expander("Recent Transactions"):
        st.dataframe(recent, hide_index=True)   

start_app()