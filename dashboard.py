import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.graph_objects as go
from portfolio_backtester import (
    create_database_tables,
    get_portfolio_returns,
    get_benchmark_returns,
    get_monthly_returns
)

chart_colors = {
    'Momentum':"#10CF9B", 
    'Value':"#50A1E7", 
    'Quality':"#23C3CB",
    'SPY Benchmark': "#15447E"
}

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
    get_monthly_returns()
    monthly_returns = pd.read_sql("SELECT * FROM monthly_returns", conn)
    monthly_returns["date"] = pd.to_datetime(monthly_returns["date"])
    return values, transactions, monthly_returns

def start_app():
    values, transactions, monthly_returns = get_data()
    values = values.pivot(index='date', columns='portfolio_name', values='portfolio_value')
    summary_df = get_calculations_summary(values)
    st.set_page_config(page_title="Portfolio Backtest Dashboard", layout="wide")
    st.title("Portfolio Backtester")
    portfolio_list = values.columns.tolist() 
    portfolio_list.append(portfolio_list.pop(portfolio_list.index('SPY Benchmark')))
    selected_portfolios = st.multiselect("Select portfolios to analyze:", portfolio_list, default=portfolio_list)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "Risk vs. Return", "Annual Returns", "Drawdowns", "Rolling Sharpe"]
    )
    with tab1: 
        st.subheader("Portfolio Performance Summary")
        get_summary_chart(selected_portfolios, summary_df)
        st.subheader("Portfolio Value Over Time")
        get_values_chart(selected_portfolios, values)
    with tab2:
        st.subheader("Risk vs. Return")
        get_risk_returns_chart(selected_portfolios, summary_df)
    with tab3:
        st.subheader("Annual Returns")    
        get_annual_returns_chart(monthly_returns,selected_portfolios)
    with tab4:
        st.subheader("Drawdowns Over Time")    
        get_drawdowns_chart(selected_portfolios, values)
    with tab5:
        st.subheader("Rolling Sharpe Ratio")
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
    summary_df = pd.DataFrame(summary).sort_values(["Sharpe"])    
    return summary_df

def get_summary_chart(selected_portfolios, summary_df):
    mask = summary_df['Portfolio'].isin(selected_portfolios)
    filtered_df = summary_df[mask]
    styled_df = filtered_df.style.format(
        "{:.2%}", subset=['CAGR', 'Volatility', 'Max Drawdown']
    ).format(
        "{:.2f}", subset=['Sharpe']
    )
    st.dataframe(
        styled_df, 
        use_container_width=True, 
        hide_index=True, 
        column_config = {
            "Sharpe": {"width": 90},
            "CAGR": {"width": 90},
            "Portfolio": {"width": 90},
            "Volatility": {"width": 90},
            "Max Drawdown": {"width": 90}
        }
    )  

def get_values_chart(selected_portfolios, values):
    fig_value = go.Figure()
    for col in selected_portfolios:
        fig_value.add_trace(
            go.Scattergl(
                x=values.index, 
                y=values[col], 
                mode='lines', 
                name=col,
                line=dict(color=chart_colors[col])
            )
        )
    fig_value.update_layout(
        yaxis_title="Portfolio Value ($)", 
        xaxis_title="Date", 
        legend_title="Portfolio", 
        hovermode="x unified", 
        template="simple_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_value, theme=None, use_container_width=True)

def get_risk_returns_chart(selected_portfolios, summary_df):
    fig_rr = go.Figure()
    summary_df_copy = summary_df.copy()        
    min_s = summary_df_copy["Sharpe"].min()
    max_s = summary_df_copy["Sharpe"].max()
    for col in selected_portfolios:
        cagr_value = summary_df_copy.loc[summary_df_copy['Portfolio'] == col, 'CAGR'].values[0]
        vol_value = summary_df_copy.loc[summary_df_copy['Portfolio'] == col, 'Volatility'].values[0]
        sharpe_value = summary_df_copy.loc[summary_df_copy['Portfolio'] == col, 'Sharpe'].values[0]        
        scaled_size = 20 + ((sharpe_value - min_s) / (max_s - min_s)) * 16
        fig_rr.add_trace(
            go.Scatter(
                x=[vol_value], 
                y=[cagr_value], 
                mode='markers+text', 
                name=col, 
                textposition="bottom left", 
                text=col,
                marker=dict(color=chart_colors[col], size=(scaled_size)),
                hovertemplate=
                "CAGR: %{y:.2%}<br>" +
                "Volatility: %{x:.2%}<br>" +
                f"Sharpe: {sharpe_value:.2f}" +
                "<extra></extra>"
            )
        )
    fig_rr.update_layout(
        xaxis_title = 'Volatility (%)',
        yaxis=dict(title='CAGR (%)', scaleanchor="x", scaleratio=1),
        showlegend=False,
        template='plotly_white',
        plot_bgcolor="rgba(0,0,0,0)",  
        paper_bgcolor="rgba(0,0,0,0)" 
    )
    st.plotly_chart(fig_rr, use_container_width=True, theme=None)

def get_annual_returns_chart(monthly_returns, selected_portfolios):
    annual_returns = (
        monthly_returns.groupby([monthly_returns["date"].dt.year, "portfolio_name"])["monthly_return"]
        .apply(lambda x: (1 + x).prod() - 1)
        .reset_index(name="annual_return")
    )
    annual_returns_df = annual_returns.pivot(index='portfolio_name', columns='date', values='annual_return')   
    annual_returns_df.index.name = 'Portfolio'
    mask = annual_returns_df.index.isin(selected_portfolios)
    filtered_df = annual_returns_df[mask].sort_values(by=2021)
    styled_table = filtered_df.style.background_gradient(
        cmap='RdBu', 
        vmin=-.3, 
        vmax=.3,
        axis=None 
    ).format(
        "{:.2%}"
    )
    st.dataframe(styled_table, use_container_width=True)

def get_drawdowns_chart(selected_portfolios, values):
    drawdowns = values[selected_portfolios] / values[selected_portfolios].cummax() - 1    
    fig_dd = go.Figure()
    for col in selected_portfolios:
        fig_dd.add_trace(
            go.Scattergl(
                x=drawdowns.index, 
                y=drawdowns[col], 
                mode='lines', 
                name=col, 
                line=dict(color=chart_colors[col])
            )
        )
    fig_dd.update_layout(
        xaxis_title="Date",
        yaxis=dict(title='Drawdown (%)', tickformat=".2%"),
        legend_title="Portfolio",
        hovermode="x unified",
        template="simple_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_dd, use_container_width=True, theme=None)

def get_rolling_charts(selected_portfolios, values):
    window = 252
    fig_rm = go.Figure()
    for col in selected_portfolios:
        daily_returns = values[col].pct_change().dropna()
        rolling_sharpe = (daily_returns.rolling(window).mean() / daily_returns.rolling(window).std()) * np.sqrt(252)
        fig_rm.add_trace(
            go.Scattergl(
                x=rolling_sharpe.index, 
                y=rolling_sharpe, 
                mode='lines', 
                name=col, 
                line=dict(color=chart_colors[col])
            )
        )
    fig_rm.add_hline(y=0, line_dash="dot", opacity=0.6)
    fig_rm.add_hline(y=1, line_dash="dot", opacity=0.6)
    fig_rm.update_layout(
        yaxis=dict(title="Sharpe Ratio", tickformat=".2f"),
        xaxis_title="Date", 
        legend_title="Portfolio",
        hovermode="x unified", 
        template="simple_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    ) 
    st.plotly_chart(fig_rm, use_container_width=True, theme=None)

def get_recent_transactions(transactions):
    recent = transactions.sort_values(["date"]).tail(20)
    recent.columns = recent.columns.str.replace('_', ' ').str.title()
    recent['Date'] = recent['Date'].dt.date
    recent['Action'] = recent['Action'].str.title()
    with st.expander("Recent Transactions"):
        st.dataframe(recent, hide_index=True)   

start_app()