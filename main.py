from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        tickers = request.form['tickers'].split(',')
        weights = list(map(float, request.form['weights'].split(',')))

        if len(weights) != len(tickers):
            return "Error: The number of weights does not match the number of tickers."

        # Fetch data with synchronized date range
        portfolio_data, start_date, end_date = get_portfolio_data(tickers)
        correlation_matrix = calculate_correlation_matrix(portfolio_data)
        annual_return, annual_std_dev = calculate_portfolio_metrics(portfolio_data, weights)

        # Convert the DataFrame to HTML for rendering
        metrics_df = pd.DataFrame({
            'Annual Return (%)': [annual_return],
            'Annual Standard Deviation (%)': [annual_std_dev]
        }, index=['Portfolio'])

        metrics_html = metrics_df.to_html(border=0, classes='styled-table', index_names=False)

        return render_template('results.html', 
                               correlation_matrix=correlation_matrix,
                               metrics_df=metrics_html,
                               start_date=start_date,
                               end_date=end_date)

    return render_template('index.html')

def get_portfolio_data(tickers):
    # Download historical data for all tickers
    all_data = {ticker: yf.download(ticker, start="1900-01-01") for ticker in tickers}

    # Determine the latest start date and earliest end date for all tickers
    start_dates = [data.index.min() for data in all_data.values()]
    end_dates = [data.index.max() for data in all_data.values()]

    start_date = max(start_dates).strftime('%Y-%m-%d')
    end_date = min(end_dates).strftime('%Y-%m-%d')

    # Re-fetch the data using the synchronized date range
    data = yf.download(tickers, start=start_date, end=end_date)
    daily_returns = data['Adj Close'].pct_change().dropna()
    return daily_returns, start_date, end_date

def calculate_correlation_matrix(daily_returns):
    # Calculate the correlation matrix
    correlation_matrix = daily_returns.corr()
    return correlation_matrix.to_html(border=0, classes='styled-table', index_names=False)

def calculate_portfolio_metrics(daily_returns, weights):
    # Calculate portfolio daily returns
    portfolio_returns = daily_returns.dot(weights)

    # Calculate annualized return and standard deviation
    annual_return = portfolio_returns.mean() * 252 * 100
    annual_std_dev = portfolio_returns.std() * (252 ** 0.5) * 100

    # Round to 2 decimal places
    annual_return = round(annual_return, 2)
    annual_std_dev = round(annual_std_dev, 2)

    return annual_return, annual_std_dev

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')



