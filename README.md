# Investment Portfolio Backtester
<table>
  <tr>
    <td>
    A portfolio backtesting engine built with Python, SQLite data storage, and a Streamlit dashboard that simulates investment strategies, tracks transactions, and visualizes portfolio performance. The project evaluates different portfolio allocations and compares them to a benchmark using performance metrics such as CAGR, volatility, Sharpe ratio, and maximum drawdown.
    </td>
  </tr>
</table> 

#### :link: <a href="https://investment-portfolio-backtester.streamlit.app/">Dashboard</a></b>

### Technologies
- Python 3.12+
- Pandas
- NumPy
- Plotly
- Streamlit
- SQL
- SQLite
- Yfinance

### Features
- Simulate multiple portfolio strategies with rebalancing and transaction tracking
- Store and query portfolio values and transactions in SQLite
- Calculate key performance metrics: CAGR, volatility, Sharpe ratio, and maximum drawdown
- Compare strategies against a benchmark (S&P 500)
- Interactive Streamlit dashboard for performance analysis
- Data visualization and charts with Plotly

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
   $ streamlit run dashboard.py
   ```

### License 
This project is MIT licensed.