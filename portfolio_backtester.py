import pandas as pd
import sqlite3
import yfinance as yf

conn = sqlite3.connect("portfolio.db")
cursor = conn.cursor()

def create_database_tables():
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
    cursor.execute("INSERT OR REPLACE INTO portfolios VALUES ('Momentum','MTUM',1)")
    cursor.execute("INSERT OR REPLACE INTO portfolios VALUES ('Momentum','AGG',0)")
    cursor.execute("INSERT OR REPLACE INTO portfolios VALUES ('Value','VTV',1)")
    cursor.execute("INSERT OR REPLACE INTO portfolios VALUES ('Value','AGG',0)")
    cursor.execute("INSERT OR REPLACE INTO portfolios VALUES ('Quality','QUAL',1)")
    cursor.execute("INSERT OR REPLACE INTO portfolios VALUES ('Quality','AGG',0)")
    conn.commit()

def get_portfolio_prices():
    tickers = ['MTUM', 'VTV', 'QUAL', 'AGG']
    start = "2015-01-01"
    end = "2025-01-01"
    data = yf.download(tickers, start=start, end=end, progress=False)
    price_data = data['Close']
    price_data.index = pd.to_datetime(price_data.index)
    return price_data

def get_benchmark_prices():
    start = "2015-01-01"
    end = "2025-01-01"
    data = yf.download("SPY", start=start, end=end, progress=False)
    benchmark = data["Close"].squeeze() 
    benchmark.index = pd.to_datetime(benchmark.index)
    return benchmark

def get_portfolio_returns(initial_investment=10000):
    prices = get_portfolio_prices()
    cursor.execute("DELETE FROM portfolio_values")
    cursor.execute("DELETE FROM transactions")
    conn.commit()
    portfolios_df = pd.read_sql("SELECT * FROM portfolios", conn)
    portfolio_names = portfolios_df['portfolio_name'].unique()
    for portfolio_name in portfolio_names:
        weights_df = portfolios_df[portfolios_df['portfolio_name'] == portfolio_name]
        weights = dict(zip(weights_df['ticker'], weights_df['weight']))
        portfolio_value = initial_investment
        period_prices = prices.copy()
        shares = {}
        first_date = period_prices.index[0]
        for ticker, weight in weights.items():
            price = float(period_prices.iloc[0][ticker])
            shares[ticker] = (portfolio_value * weight) / price
            cursor.execute("""
            INSERT OR REPLACE INTO transactions
            VALUES (?,?,?,?,?,?)
            """, (str(first_date.date()), portfolio_name, ticker, "buy", shares[ticker], price))
        daily_value = (period_prices * pd.Series(shares)).sum(axis=1)
        for date, value in daily_value.items():
            cursor.execute("""
            INSERT OR REPLACE INTO portfolio_values
            VALUES (?,?,?)
            """, (str(date), portfolio_name, float(value)))   
    conn.commit()

def get_benchmark_returns(initial_investment=10000):
    benchmark = get_benchmark_prices()
    returns = benchmark.pct_change().dropna()
    benchmark_value = (1 + returns).cumprod() * initial_investment
    benchmark_value.index = pd.to_datetime(benchmark_value.index)
    start_date = "2015-01-02 00:00:00"
    cursor.execute("""
    INSERT OR REPLACE INTO portfolio_values
    VALUES (?,?,?)
    """, (str(start_date), "SPY Benchmark", float(initial_investment)))
    for date, value in benchmark_value.items():
        cursor.execute("""
        INSERT OR REPLACE INTO portfolio_values
        VALUES (?,?,?)
        """, (str(date), "SPY Benchmark", float(value)))
    conn.commit()

if __name__ == "__main__":
    create_database_tables()
    get_portfolio_returns()
    get_benchmark_returns()