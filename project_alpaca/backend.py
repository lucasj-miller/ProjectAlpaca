import requests
import yfinance as yf
import pandas as pd
import numpy as np

class Asset:
    def __init__(self, ticker):
        self.ticker = ticker.upper()
        self.stock_data = pd.DataFrame()
        self.market_data = pd.DataFrame()

    def get_data(self, start_date, end_date):
        """Fetches Stock and Benchmark data, returns both as a tuple"""

        # 1. Define the Benchmark (S&P 500)
        benchmark_ticker = "^GSPC"

        # 2. Download Data (Let yfinance handle the session internally)
        # We fetch a bit of buffer to ensure we have data for the start date
        self.stock_data = yf.download(self.ticker, start=start_date, end=end_date, progress=False)
        self.market_data = yf.download(benchmark_ticker, start=start_date, end=end_date, progress=False)

        # 3. Clean up MultiIndex (Fix for recent yfinance updates)
        if isinstance(self.stock_data.columns, pd.MultiIndex):
            self.stock_data.columns = self.stock_data.columns.droplevel(1)
        if isinstance(self.market_data.columns, pd.MultiIndex):
            self.market_data.columns = self.market_data.columns.droplevel(1)

        # 4. Ensure data alignment
        self.stock_data = self.stock_data.loc[start_date:]
        self.market_data = self.market_data.loc[start_date:]

        return self.stock_data, self.market_data

    def calculate_risk_metrics(self):
        """Calculates Beta, Volatility, and Sharpe Ratio"""
        if self.stock_data.empty or self.market_data.empty:
            return None

        # Calculate daily % returns
        stock_returns = self.stock_data['Close'].pct_change().dropna()
        market_returns = self.market_data['Close'].pct_change().dropna()

        # Align data
        data = pd.concat([stock_returns, market_returns], axis=1).dropna()
        data.columns = ['Stock', 'Market']

        # 1. Beta
        covariance = data['Stock'].cov(data['Market'])
        market_variance = data['Market'].var()
        beta = covariance / market_variance if market_variance != 0 else 1.0

        # 2. Volatility (Annualized)
        volatility = data['Stock'].std() * np.sqrt(252) * 100

        # 3. Sharpe Ratio (Assume 4% Risk Free)
        risk_free_rate = 0.04
        excess_return = (data['Stock'].mean() * 252) - risk_free_rate
        sharpe = excess_return / (volatility / 100) if volatility != 0 else 0

        return {
            "beta": beta,
            "volatility": volatility,
            "sharpe": sharpe
        }

    def get_news(self, limit=3):
        """Fetches and cleans news articles"""
        tick_obj = yf.Ticker(self.ticker)
        raw_news = tick_obj.news
        clean_news = []
        
        if raw_news:
            for item in raw_news[:limit]:
                content = item.get('content', {})
                url_data = content.get('clickThroughUrl') or content.get('canonicalUrl')
                
                article = {
                    "title": content.get('title', 'No Title'),
                    "link": url_data.get('url', '#') if url_data else '#',
                    "publisher": content.get('provider', {}).get('displayName', 'Unknown')
                }
                clean_news.append(article)
        
        return clean_news

    # Add this method to the Asset class in backend.py
    def calculate_risk(self, stock_data, market_data):
        # Calculates Beta, Sharpe, and Volatility
        try:
            # 1. Calculate Daily Returns
            stock_returns = stock_data['Close'].pct_change().dropna()
            market_returns = market_data['Close'].pct_change().dropna()

            # Align data (ensure same dates)
            data = pd.DataFrame({'Stock': stock_returns, 'Market': market_returns}).dropna()

            # 2. Beta Calculation (Covariance / Variance)
            covariance = data['Stock'].cov(data['Market'])
            market_variance = data['Market'].var()
            beta = covariance / market_variance

            # 3. Annualized Volatility
            volatility = data['Stock'].std() * (252 ** 0.5)

            # 4. Sharpe Ratio (assuming 4% risk-free rate)
            rf_rate = 0.04
            excess_return = data['Stock'].mean() * 252 - rf_rate
            sharpe = excess_return / volatility

            return {
                "beta": beta,
                "volatility": volatility,
                "sharpe": sharpe
            }
        except Exception as e:
            return {"beta": None, "volatility": None, "sharpe": None}

    def get_fundamentals(self):
        # Calculates metrics from raw data (fast_info, financials)
        try:
            ticker_obj = yf.Ticker(self.ticker)
            # Get Price and Market Cap
            try:
                price = ticker_obj.info['currentPrice']
                market_cap = ticker_obj.info['marketCap']
            except:
                price = None
                market_cap = None
            # Calculate Dividend Yield
            div_yield = None
            try:
                divs = ticker_obj.dividends
                oneyear = pd.Timestamp.now().tz_localize(divs.index.dtype.tz) - pd.Timedelta(days=365)
                recent_divs = divs[divs.index >= oneyear]
                if not recent_divs.empty and price:
                    total_div = recent_divs.sum()
                    div_yield = total_div / price
            except:
                div_yield = None
            # Calculate P/E Ratio
            pe_ratio = None
            try:
                stmt = ticker_obj.income_stmt
                if not stmt.empty:
                    eps = None
                    if 'Diluted EPS' in stmt.index:
                        eps = stmt.loc['Diluted EPS'].iloc[0]
                    elif 'Basic EPS' in stmt.index:
                        eps = stmt.loc['Basic EPS'].iloc[0]
                    if eps and price:
                        pe_ratio = price / eps
            except:
                pe_ratio = None
            return {
                "market_cap": market_cap,
                "pe_ratio": pe_ratio,
                "dividend_yield": div_yield,
                "eps": eps
            }
        except Exception as e:
            return {"error": str(e)}
