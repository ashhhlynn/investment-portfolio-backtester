# Investment Portfolio Backtester
<table>
  <tr>
    <td>
    A portfolio backtesting engine built with Python, SQLite data storage, and a Streamlit dashboard that simulates investment strategies, tracks transactions, and visualizes portfolio performance. The project evaluates different portfolio allocations and compares them to a benchmark using performance metrics such as CAGR, volatility, Sharpe ratio, and maximum drawdown.
    </td>
  </tr>
</table> 

### Technologies
- Python 3.8+
- Pandas
- NumPy
- Plotly
- Streamlit
- SQL
- SQLite

### Features
- Simulate multiple portfolio strategies with rebalancing and transaction tracking
- Store and query portfolio values and transactions in SQLite
- Calculate key performance metrics: CAGR, volatility, Sharpe ratio, and maximum drawdown
- Compare strategies against a benchmark (S&P 500)
- Interactive Streamlit dashboard for performance analysis
#### Example Strategies
The project currently includes several example portfolio allocations:
- Aggressive: 80% SPY / 20% AGG
- Balanced: 60% SPY / 40% AGG
- Conservative: 40% SPY / 60% AGG

### Setup 
   ```sh
   $ git clone https://github.com/ashhhlynn/investment-portfolio-backtester.git
   ```
   ```sh
   $ cd investment-portfolio-backtester
   ```
   ```sh
   $ pip install -r requirements.txt
   ```
   ```sh
   $ python portfolio_backtester.py
   ```
   ```sh
   $ streamlit run dashboard.py
   ```

### License 
This project is MIT licensed.
