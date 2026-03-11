import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas_datareader.data as web
from datetime import datetime


def get_portfolio_prices():
    tickers = ['SPY', 'AGG']
    start = datetime(2015,1,1)
    end = datetime(2025,1,1)
    price_data = pd.DataFrame()
    for ticker in tickers:
        df = web.DataReader(ticker, 'stooq', start, end)['Close'].sort_index()
        price_data[ticker] = df
    price_data.index = pd.to_datetime(price_data.index)
    return price_data

def get_benchmark_prices():
    start = datetime(2015,1,1)
    end = datetime(2025,1,1)
    benchmark = web.DataReader('SPY', 'stooq', start, end)['Close'].sort_index()
    benchmark.index = pd.to_datetime(benchmark.index)
    return benchmark

def get_portfolio_returns(initial_investment=10000, rebalance_frequency='Y'):
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    prices = get_portfolio_prices()
    returns = prices.pct_change().dropna()
    cursor.execute("DELETE FROM portfolio_values")
    cursor.execute("DELETE FROM transactions")
    conn.commit()
    rebalance_dates = returns.resample(rebalance_frequency).first().index
    portfolios_df = pd.read_sql("SELECT * FROM portfolios", conn)
    portfolio_names = portfolios_df['portfolio_name'].unique()
    for portfolio_name in portfolio_names:
        weights_df = portfolios_df[portfolios_df['portfolio_name'] == portfolio_name]
        weights = dict(zip(weights_df['ticker'], weights_df['weight']))
        portfolio_value = initial_investment
        for i in range(len(rebalance_dates)-1):
            start = rebalance_dates[i]
            end = rebalance_dates[i+1]
            period_prices = prices.loc[start:end]
            shares = {}
            for ticker, weight in weights.items():
                price = float(period_prices.iloc[0][ticker])
                shares[ticker] = (portfolio_value * weight) / price
                cursor.execute("""
                INSERT OR REPLACE INTO transactions
                VALUES (?,?,?,?,?,?)
                """, (str(start.date()), portfolio_name, ticker, "buy", shares[ticker], price))
            daily_value = (period_prices * pd.Series(shares)).sum(axis=1)
            for date, value in daily_value.items():
                cursor.execute("""
                INSERT OR REPLACE INTO portfolio_values
                VALUES (?,?,?)
                """, (str(date.date()), portfolio_name, float(value)))
            portfolio_value = float(daily_value.iloc[-1])
    conn.commit()

def get_benchmark_returns(initial_investment=10000):
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    benchmark = get_benchmark_prices()
    returns = benchmark.pct_change().dropna()
    benchmark_value = (1 + returns).cumprod() * initial_investment
    benchmark_value.index = pd.to_datetime(benchmark_value.index)
    for date, value in benchmark_value.items():
        cursor.execute("""
        INSERT OR REPLACE INTO portfolio_values
        VALUES (?,?,?)
        """, (str(date.date()), "SPY Benchmark", float(value)))
    conn.commit()

def plot_results():
    conn = sqlite3.connect("portfolio.db")
    values = pd.read_sql("SELECT * FROM portfolio_values", conn)
    values['date'] = pd.to_datetime(values['date'])
    values = values.pivot(index='date', columns='portfolio_name', values='portfolio_value')
    plt.figure(figsize=(12,6))
    for column in values.columns:
        if column == "SPY Benchmark":
            plt.plot(values.index, values[column], linestyle="--", color="black", label=column)
        else:
            plt.plot(values.index, values[column], label=column)
    plt.title("Portfolio Strategies vs S&P 500 Benchmark")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value ($)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("portfolio_backtest.png")

def performance_summary():
    conn = sqlite3.connect("portfolio.db")
    values = pd.read_sql("SELECT * FROM portfolio_values", conn)
    values['date'] = pd.to_datetime(values['date'])
    values = values.pivot(index='date', columns='portfolio_name', values='portfolio_value')
    summary = []
    for portfolio_name in values.columns:
        series = values[portfolio_name]
        series = series.dropna()
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
    print(summary_df)

def plot_all(save_folder="plots"):
    conn = sqlite3.connect("portfolio.db")
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    values = pd.read_sql("SELECT * FROM portfolio_values", conn)
    values['date'] = pd.to_datetime(values['date'])
    values = values.pivot(index='date', columns='portfolio_name', values='portfolio_value')
    plt.figure(figsize=(12,6))
    for col in values.columns:
        if col == "SPY Benchmark":
            plt.plot(values.index, values[col], linestyle="--", color="black", label=col)
        else:
            plt.plot(values.index, values[col], label=col)
    plt.title("Portfolio Strategies vs S&P 500 Benchmark")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value ($)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{save_folder}/portfolio_vs_benchmark.png")
    plt.close()
    plt.figure(figsize=(12,6))
    for col in values.columns:
        cumulative_max = values[col].cummax()
        drawdown = (values[col] - cumulative_max) / cumulative_max
        plt.plot(drawdown, label=col)
    plt.title("Portfolio Drawdowns Over Time")
    plt.ylabel("Drawdown")
    plt.xlabel("Date")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{save_folder}/drawdowns.png")
    plt.close()
    monthly_returns = values.resample('M').last().pct_change().dropna()
    plt.figure(figsize=(12,6))
    for col in monthly_returns.columns:
        plt.hist(monthly_returns[col], bins=50, alpha=0.5, label=col)
    plt.title("Monthly Returns Distribution")
    plt.xlabel("Return")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{save_folder}/monthly_returns_hist.png")
    plt.close()
    plt.figure(figsize=(12,6))
    window = 252
    for col in values.columns:
        daily_returns = values[col].pct_change().dropna()
        rolling_sharpe = (daily_returns.rolling(window).mean() / daily_returns.rolling(window).std()) * np.sqrt(252)
        plt.plot(rolling_sharpe, label=col)
    plt.title(f"{window}-Day Rolling Sharpe Ratio")
    plt.xlabel("Date")
    plt.ylabel("Rolling Sharpe")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{save_folder}/rolling_sharpe.png")
    plt.close()
    plt.figure(figsize=(12,6))
    for col in values.columns:
        daily_returns = values[col].pct_change().dropna()
        rolling_vol = daily_returns.rolling(window).std() * np.sqrt(252)
        plt.plot(rolling_vol, label=col)
    plt.title(f"{window}-Day Rolling Volatility")
    plt.xlabel("Date")
    plt.ylabel("Annualized Volatility")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{save_folder}/rolling_volatility.png")
    plt.close()

# if __name__ == "__main__":
#   run_backtester()

def run_backtester():
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_name TEXT,
    ticker TEXT,
    weight REAL,
    PRIMARY KEY (portfolio_name, ticker)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio_values (
    date TEXT,
    portfolio_name TEXT,
    portfolio_value REAL,
    PRIMARY KEY (date, portfolio_name)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
    date TEXT,
    portfolio_name TEXT,
    ticker TEXT,
    action TEXT,
    shares REAL,
    price REAL,
    PRIMARY KEY(date, portfolio_name, ticker, action)
    )
    """)
    conn.commit()
    cursor.execute("INSERT OR REPLACE INTO portfolios VALUES ('Aggressive','SPY',0.8)")
    cursor.execute("INSERT OR REPLACE INTO portfolios VALUES ('Aggressive','AGG',0.2)")
    cursor.execute("INSERT OR REPLACE INTO portfolios VALUES ('Balanced','SPY',0.6)")
    cursor.execute("INSERT OR REPLACE INTO portfolios VALUES ('Balanced','AGG',0.4)")
    cursor.execute("INSERT OR REPLACE INTO portfolios VALUES ('Conservative','SPY',0.4)")
    cursor.execute("INSERT OR REPLACE INTO portfolios VALUES ('Conservative','AGG',0.6)")
    conn.commit()
    get_portfolio_returns()
    get_benchmark_returns()
    performance_summary()