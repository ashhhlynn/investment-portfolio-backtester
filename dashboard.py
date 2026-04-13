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

chart_colors = {
    'Momentum':"#0ED09C", 
    'Value':"#50A1E7", 
    'Quality':"#17becf",
    'SPY Benchmark': "#15447E"
}

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
        get_recent_transactions(transactions)
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
            "Sharpe Ratio": sharpe,
            "Max Drawdown": max_dd
        })
    summary_df = pd.DataFrame(summary).sort_values(["Sharpe Ratio"], ascending=False)    
    return summary_df

def get_summary_chart(selected_portfolios, summary_df):
    mask = summary_df['Portfolio'].isin(selected_portfolios)
    filtered_df = summary_df[mask]
    styled_df = filtered_df.style.apply(
        highlight_winners
    ).apply(
        highlight_losers
    ).format(
        "{:.2%}", subset=['CAGR', 'Volatility', 'Max Drawdown']
    ).format(
        "{:.2f}", subset=['Sharpe Ratio']
    )
    st.dataframe(
        styled_df, 
        use_container_width=False, 
        hide_index=True, 
        column_config = {
            "Sharpe Ratio": {"width": 220},
            "CAGR": {"width": 220},
            "Portfolio": {"width": 220},
            "Volatility": {"width": 220},
            "Max Drawdown": {"width": 220}
        }  
    )  

def highlight_winners(column):
    if column.name in ['CAGR', 'Sharpe Ratio', 'Max Drawdown']:
        is_winner = column == column.max()
    elif column.name in ['Volatility']:
        is_winner = column == column.min() 
    else:
        return [''] * len(column)
    return ['background-color: white; color: #2475c3; font-weight: bold' if v else '' for v in is_winner]

def highlight_losers(column):
    if column.name in ['CAGR', 'Sharpe Ratio', 'Max Drawdown']:
        is_loser = column == column.min()
    elif column.name in ['Volatility']:
        is_loser = column == column.max() 
    else:
        return [''] * len(column)
    return ['background-color: white; color:#707b90' if v else '' for v in is_loser]

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
        hovermode="x unified", 
        template="simple_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_value, theme=None, use_container_width=True)

def get_risk_returns_chart(selected_portfolios, summary_df):
    fig_rr = go.Figure()
    summary_df_copy = summary_df.copy()        
    min_s = summary_df_copy["Sharpe Ratio"].min()
    max_s = summary_df_copy["Sharpe Ratio"].max()
    for col in selected_portfolios:
        cagr_value = summary_df_copy.loc[summary_df_copy['Portfolio'] == col, 'CAGR'].values[0]
        vol_value = summary_df_copy.loc[summary_df_copy['Portfolio'] == col, 'Volatility'].values[0]
        sharpe_value = summary_df_copy.loc[summary_df_copy['Portfolio'] == col, 'Sharpe Ratio'].values[0]        
        scaled_size = 20 + (sharpe_value - min_s) / (max_s - min_s) * 20
        fig_rr.add_trace(
            go.Scatter(
                x=[vol_value], 
                y=[cagr_value], 
                mode='markers', 
                name=col, 
                marker=dict(color=chart_colors[col], size=(scaled_size)),
                hovertemplate=
                "<extra></extra>" +
                "<b>CAGR:</b> %{y:.2}<br>" +
                "<b>Volatility:</b> %{x:.2}<br>" +
                f"<b>Sharpe:</b> {sharpe_value:.2f}" 
            )
        )
    fig_rr.add_trace(go.Scatter(
        x=[None], 
        y=[None],
        mode='markers',
        marker=dict(size=20, color='gray'),
        legendgroup='size',
        name='Size: Sharpe'
    ))
    fig_rr.update_layout(
        xaxis=dict(title='Volatility', tickformat=".0%"),
        yaxis=dict(title='CAGR', tickformat=".0%", scaleanchor="x", scaleratio=1),
        showlegend=True,
        template='plotly_white',
        plot_bgcolor="rgba(0,0,0,0)",  
        paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel_align = 'right'
    )
    st.plotly_chart(fig_rr, use_container_width=True, theme=None)

def get_annual_returns_chart(monthly_returns, selected_portfolios):
    annual_returns = (
        monthly_returns.groupby([monthly_returns["date"].dt.year, "portfolio_name"])["monthly_return"].apply(
            lambda x: (1 + x).prod() - 1
        ).reset_index(
            name="annual_return"
        )
    )
    annual_returns_df = annual_returns.pivot(index='portfolio_name', columns='date', values='annual_return')   
    annual_returns_df.index.name = 'Portfolio'
    mask = annual_returns_df.index.isin(selected_portfolios)
    filtered_df = annual_returns_df[mask]
    if 'SPY Benchmark' in filtered_df.index:
        benchmark_values = filtered_df.loc['SPY Benchmark']
        filtered_df['Beating'] = (filtered_df > benchmark_values).sum(axis=1)
    else:
        filtered_df['Beating'] = 0
    filtered_df = filtered_df.sort_values(['Beating'], ascending=False)
    cols_to_style = [c for c in filtered_df.columns if c != 'Beating']
    styled_table = filtered_df.style.apply(
        bold_outperformers, 
        axis=None
    ).background_gradient(
        cmap='RdBu', 
        vmin=-.3, 
        vmax=.3,
        axis=None,
        subset=cols_to_style
    ).set_properties(
        **{'background-color': '#f7fbff', 'width':'50px'}, 
        subset=['Beating']
    ).format(
        "{:.2%}", 
        subset=cols_to_style
    )
    st.dataframe(
        styled_table, 
        use_container_width=True, 
        column_config={"Beating": st.column_config.Column(width=40)}
    )

def bold_outperformers(data):
    style_df = pd.DataFrame('', index=data.index, columns=data.columns)
    if 'SPY Benchmark' in data.index:
        benchmark_row = data.loc['SPY Benchmark']
        is_outperformer = data > benchmark_row
        style_df = is_outperformer.applymap(lambda x: 'font-weight: bold;' if x else '')
        style_df.loc['SPY Benchmark'] = ''        
    return style_df

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
        yaxis=dict(title='Drawdown', tickformat=".2%"),
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