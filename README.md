# Investment Portfolio Backtester
<table>
  <tr>
    <td>
    A portfolio backtester built with Python, SQLite data storage, and a Streamlit dashboard to simulate factor-based investment strategies. The project evaluates portfolios against an S&P 500 benchmark using performance metrics such as CAGR, volatility, Sharpe ratio, and drawdowns, with interactive visualizations for analyzing risk, return, and growth over time.
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
- Store and query historical ETF data using SQLite
- Compute key performance metrics: CAGR, volatility, Sharpe ratio, maximum drawdown and duration
- Interactive Streamlit dashboard for analyzing risk-adjusted performance and consistency across portfolios
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
