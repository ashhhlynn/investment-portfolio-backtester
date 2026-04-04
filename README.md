# Investment Portfolio Backtester
<table>
  <tr>
    <td>
    A portfolio backtesting engine built with Python, SQLite data storage, and a Streamlit dashboard to simulate factor-based investment strategies. The project evaluates portfolios against an S&P 500 benchmark using performance metrics such as CAGR, volatility, Sharpe ratio, and maximum drawdown, with interactive visualizations for analyzing risk, return, and consistency over time.

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
- Simulate and compare multiple portfolio strategies against an S&P 500 benchmark
- Store and query portfolio data using SQLite
- Compute key performance metrics: CAGR, volatility, Sharpe ratio, and maximum drawdown
- Interactive Streamlit dashboard for analyzing risk, return, and consistency across portfolios
- Plotly charts to visualize growth over time, drawdowns, rolling Sharpe, and risk-return comparisons

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