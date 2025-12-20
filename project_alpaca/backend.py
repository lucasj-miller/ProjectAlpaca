import yfinance as yf
import pandas as pd
import numpy as np

class Asset:
    def __init__(self, ticker):
        self.ticker = ticker.upper()
        self.stock_data = pd.DataFrame()
        self.market_data = pd.DataFrame()

    def get_data(self, start_date, end_date):
        """Fetches Stock and Market (S&P500) data"""
        self.stock_data = yf.download(self.ticker, start=start_date, end=end_date, progress=False)
        self.market_data = yf.download("^GSPC", start=start_date, end=end_date, progress=False)
        
        # Clean MultiIndex (Standard yfinance fix)
        if isinstance(self.stock_data.columns, pd.MultiIndex):
            self.stock_data.columns = self.stock_data.columns.droplevel(1)
        if isinstance(self.market_data.columns, pd.MultiIndex):
            self.market_data.columns = self.market_data.columns.droplevel(1)
            
        return self.stock_data

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