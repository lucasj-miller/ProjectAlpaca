import yfinance as yf
import pandas as pd
import numpy as np
import wikipedia

class Asset:
    def __init__(self, ticker):
        self.ticker = ticker.upper()
        self.stock_data = pd.DataFrame()
        self.market_data = pd.DataFrame()

    # == Fetches Stock and Benchmark (S&P 500) Data ==
    def get_data(self, start_date, end_date):
        # 1. Define the Benchmark (S&P 500)
        benchmark_ticker = "^GSPC"

        # 2. Download Data for both Stock and Benchmark
        self.stock_data = yf.download(self.ticker, start=start_date, end=end_date, progress=False)
        self.market_data = yf.download(benchmark_ticker, start=start_date, end=end_date, progress=False)

        # 3. Clean up MultiIndex (Fix for recent yfinance updates)
        if isinstance(self.stock_data.columns, pd.MultiIndex):
            self.stock_data.columns = self.stock_data.columns.droplevel(1)
        if isinstance(self.market_data.columns, pd.MultiIndex):
            self.market_data.columns = self.market_data.columns.droplevel(1)

        # 4. Ensure Data Aligns with Each Other
        self.stock_data = self.stock_data.loc[start_date:]
        self.market_data = self.market_data.loc[start_date:]

        return self.stock_data, self.market_data

    # == Calculates Risk Metrics (Beta, Volatility, Sharpe Ratio) ==
    def calculate_risk_metrics(self):
        # If empty, return None
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

    # == Fetch recent news on the Stock ==
    def get_news(self, limit=3):
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

    # == Use raw yfinance data to fetch additional fundamentals ==
    def get_fundamentals(self, current_price=None):
        data = {
            "market_cap": None,
            "pe_ratio": None,
            "eps": None,
            "dividend_yield": None,
            "description": None,
            "name": self.ticker
        }

        try:
            tick = yf.Ticker(self.ticker)

            # GET COMPANY NAME (for Wikipedia search)
            # Try multiple keys because yfinance can be inconsistent
            try:
                # check shortName (e.g. "Fossil Group, Inc.")
                name = tick.info.get('shortName')
                if not name:
                    name = tick.info.get('longName')
                if name:
                    data["name"] = name
            except:
                pass

            # MARKET CAP (Try fast_info, fallback to info)
            try:
                # Primary method
                data["market_cap"] = tick.fast_info['market_cap']
            except:
                # Fallback method (slower but sometimes works when fast_info fails)
                try:
                    data["market_cap"] = tick.info.get('marketCap')
                except:
                    pass

            # EPS
            eps = None
            try:
                stmt = tick.income_stmt
                if not stmt.empty:
                    possible_keys = ['Diluted EPS', 'Basic EPS', 'DilutedEPS']
                    for key in possible_keys:
                        if key in stmt.index:
                            eps = stmt.loc[key].iloc[0]
                            break
                    data["eps"] = eps
            except:
                pass

            # 3. P/E RATIO
            if current_price is None:
                try:
                    current_price = tick.fast_info['last_price']
                except:
                    pass
            # Calculate P/E using whatever price we have
            if eps and current_price:
                data["pe_ratio"] = current_price / eps

            # 4. DIVIDEND YIELD
            try:
                divs = tick.dividends
                if not divs.empty:
                    # Get dividends from last 365 days
                    one_year_ago = pd.Timestamp.now().tz_localize(divs.index.dtype.tz) - pd.Timedelta(days=365)
                    recent_divs = divs[divs.index >= one_year_ago]
                    if not recent_divs.empty and current_price:
                        data["dividend_yield"] = recent_divs.sum() / current_price
            except:
                pass

            # 5. COMPANY DESCRIPTION
            try:
                # Strategy 1: Search by Company Name (Best results)
                # e.g. Search "Fossil Group, Inc." -> specific page
                if data["name"] != self.ticker:
                    search_term = data["name"]
                else:
                    # Strategy 2: If we only have ticker, append "Inc"
                    # "FOSL Inc" will not auto-correct to "Foal"
                    search_term = f"{self.ticker} Inc"
                data["description"] = wikipedia.summary(search_term, sentences=3)
            except:
                try:
                    # Strategy 3: "Ticker + stock" (Last resort)
                    data["description"] = wikipedia.summary(f"{self.ticker} stock", sentences=3)
                except:
                    data["description"] = "Description unavailable."

            return data
        except Exception as e:
            return data