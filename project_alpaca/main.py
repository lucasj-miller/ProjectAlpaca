
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from backend import Asset  # <--- Import your new class

# 1. PAGE CONFIG
st.set_page_config(page_title="Alpaca Finance", layout="wide")

# 2. CSS STYLING
st.markdown("""
    <style>
    /* Main Background: Subtle Black Gradient */
    .stApp {
        background: linear-gradient(to bottom right, #2b2b2b, #000000);
        color: #ffffff; 
        font-family: "Roboto Mono", monospace;
    }
    
    /* 1. INPUT BOXES */
    div[data-baseweb="input"] {
        background-color: #000000 !important; /* Pure Black Background */
        border: 1px solid #444 !important;    /* Dark Gray Border */
        border-radius: 0px !important;
    }
    
    /* Input Text: White */
    input[class] {
        color: #ffffff !important;
        font-family: "Roboto Mono", monospace !important;
    }
    
    /* Focus State: Amber Glow */
    div[data-baseweb="base-input"]:focus-within {
        border: 1px solid #FF9900 !important;
    }

    /* 2. BUTTONS (Keep Amber) */
    button[kind="primary"] {
        background: linear-gradient(to bottom, #FF9900, #CC7A00) !important;
        color: #000000 !important;
        border: none;
        font-weight: bold;
        border-radius: 0px !important;
    }
    
    /* 3. METRICS */
    /* Value: White */
    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-family: "Roboto Mono", monospace;
    }
    /* Label: Light Gray */
    div[data-testid="stMetricLabel"] {
        color: #b0b0b0 !important;
    }
    
    /* 4. PLOTLY CHARTS */
    .js-plotly-plot .plotly .main-svg {
        background: rgba(0,0,0,0) !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. HEADER
col_title = st.columns([0.8, 10])
st.markdown(
    """
    <h1 style='margin-bottom: 0px; margin-top: 0px; padding-top: 10px; font-size: 3rem;'>
        🦙 Alpaca Finance Terminal
    </h1>
    """,
    unsafe_allow_html=True)

st.markdown(
    """
    <div style='background-color: #111; padding: 15px; border-radius: 5px; border-left: 5px solid #FF9900; margin-bottom: 20px;'>
        <p style='font-size: 1.0rem; color: #ddd; margin: 0; line-height: 1.5;'>
            <b>Equity Research Dashboard:</b> An institutional-grade analytics tool designed for rapid security assessment. 
            This platform integrates real-time <b>Performance Evaluation</b> (Price, Price Change), <b>Fundamental Data</b> (P/E, Market Cap), <b>Quantitative Risk Scoring</b> (Beta, Sharpe Ratio), 
            and <b>Relative Performance Analysis</b> (Alpha vs. S&P 500) to measure excess returns against the benchmark.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# 4. MAIN INTERFACE
col_input, col_result = st.columns([1, 2])

# Box for inputting name of Stock and time frame.
with col_input:
    with st.container(border=True):
        st.subheader("🛠️ Analyze Security")
        ticker = st.text_input("Ticker Symbol", placeholder="AAPL, TSLA...").upper()

        default_start = datetime.now() - timedelta(days=365)
        default_end = datetime.now()
        date_range = st.date_input("Analysis Period", (default_start, default_end))

        run_btn = st.button("Run Analysis", type="primary", width="stretch")

# 5. EXECUTION LOGIC
with col_result:
    if run_btn and ticker:
        try:
            # Loading circle
            with st.spinner(f"Analyzing {ticker}..."):
                # Initialize Asset
                asset = Asset(ticker)

                # A. Handle Dates
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start, end = date_range
                else:
                    start, end = default_start, default_end

                # B. Get Data
                stock_data, market_data = asset.get_data(start, end)

                if stock_data.empty:
                    st.error(f"No data found for {ticker}")
                else:
                    latest_price = stock_data['Close'].iloc[-1]
                    metrics = asset.calculate_risk_metrics()
                    funds = asset.get_fundamentals(latest_price)
                    # Determine Company Name
                    company_name = funds.get('name', ticker)

                    # Display Description and News in left column.
                    with col_input:
                        desc = funds.get('description')
                        if desc and desc != "Description unavailable.":
                            with st.container(border=True):
                                st.write(desc)
                        with st.container(border=True):
                            st.subheader("📰 Recent News")
                            news_items = asset.get_news()
                            if news_items:
                                for n in news_items:
                                    st.markdown(f"**[{n['title']}]({n['link']})**")
                                    st.caption(f"Source: {n['publisher']}")
                                    st.markdown("---")
                            else:
                                st.write("No news found.")

                    # Display metrics on the right column
                    with st.container(border=True):
                        # Title
                        st.markdown(
                            f"""
                            <div style='background-color: #111; padding: 15px; border-radius: 5px; border-left: 5px solid #FF9900; margin-bottom: 20px;'>
                                <p style='font-size: 1.0rem; color: #ddd; margin: 0; line-height: 1.5;'>
                                    <b>📈 {company_name}'s Recent Performance</b>
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True)

                        # Row 1: Performance
                        current_price = stock_data['Close'].iloc[-1]
                        start_price = stock_data['Close'].iloc[0]
                        profit = (current_price - start_price)
                        pct_change = ((current_price - start_price) / start_price) * 100

                        m1, m2 = st.columns(2)
                        m1.metric("Share Price", f"${current_price:,.2f}")
                        m2.metric("Price Change", f"${profit:,.2f}", delta=f"{pct_change:.2f}%")

                        # Row 2: Fundamentals
                        st.markdown(
                            f"""
                            <div style='background-color: #111; padding: 15px; border-radius: 5px; border-left: 5px solid #FF9900; margin-bottom: 20px;'>
                                <p style='font-size: 1.0rem; color: #ddd; margin: 0; line-height: 1.5;'>
                                    <b>🏢 Fundamental Data</b>
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True)

                        f1, f2, f3, f4 = st.columns(4)

                        # 1. Market Cap
                        mc = funds.get('market_cap')
                        if mc:
                            fmt_mc = f"${mc/1e12:.2f}T" if mc > 1e12 else f"${mc/1e9:.2f}B"
                            f1.metric("Market Cap", fmt_mc)
                        else:
                            f1.metric("Market Cap", "-")

                        # 2. P/E Ratio
                        pe = funds.get('pe_ratio')
                        if pe:
                            # Logic:
                            # < 0: Loss Making (Red)
                            # 0-20: Value / Cheap (Green)
                            # 20-40: Fair / Average (Grey)
                            # > 40: High Premium / Expensive (Red)

                            if pe < 0:
                                pe_col, pe_msg = "inverse", "Loss Making"
                            elif pe < 20:
                                pe_col, pe_msg = "normal", "Value"
                            elif pe < 40:
                                pe_col, pe_msg = "off", "Fair Value"
                            else:
                                pe_col, pe_msg = "inverse", "High Premium"

                            f2.metric("P/E Ratio", f"{pe:.2f}", delta=pe_msg, delta_color=pe_col)
                        else:
                            f2.metric("P/E Ratio", "-")

                        # 3. EPS
                        eps = funds.get('eps')
                        if eps:
                            if eps > 0:
                                f3.metric("EPS (TTM)", f"${eps:.2f}", delta="Positive", delta_color="normal")
                            else:
                                f3.metric("EPS (TTM)", f"${eps:.2f}", delta="Negative", delta_color="inverse")
                        else:
                            f3.metric("EPS (TTM)", "-")

                        # 4. Div Yield (Bonus if you want it)
                        div = funds.get('dividend_yield')
                        if div:
                            f4.metric("Dividend Yield", f"{div*100:.2f}%")
                        else:
                            # Fallback to Price if no div
                            f4.metric("Dividend Yield", "-")
                        with st.expander("❓ What do these metrics mean?"):
                            st.markdown("""
                            **Market Cap** 
                            * Market capitalization, or market cap, is the current market value of all of a company's outstanding stock shares. 
                            * Market cap is often used to indicate a company's size and worth in comparison to its peers.
                            
                            **P/E Ratio (Price-to-Earnings)** 
                            * The price-to-earnings (P/E) ratio measures a company's share price relative to its earnings per share (EPS). 
                            * Often called the price or earnings multiple, the P/E ratio helps assess the relative value of a company's stock.
                            * It helps to determine whether a stock is overvalued or undervalued.
                            
                            **EPS (Earnings Per Share)** 
                            * Earnings per share (EPS) is a commonly used measure of a company's profitability. 
                            * It indicates how much profit each outstanding share of common stock has earned. 
                            * Generally speaking, the higher a company's EPS, the more profitable it is considered to be.
                            
                            **Dividend Yield** 
                            * The annual percentage return paid to shareholders in dividends. 
                            * A blank value means the company does not pay dividends.
                            """)
                        # Row 3: Risk Profile
                        st.markdown(
                            f"""
                            <div style='background-color: #111; padding: 15px; border-radius: 5px; border-left: 5px solid #FF9900; margin-bottom: 20px;'>
                                <p style='font-size: 1.0rem; color: #ddd; margin: 0; line-height: 1.5;'>
                                    <b>⚠️ Risk Profile (vs S&P 500)</b>
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True)
                        r1, r2, r3 = st.columns(3)

                        if metrics:
                            # Color Logic
                            b_val = metrics['beta']
                            if b_val > 1.5:
                                b_col, b_msg = "inverse", "High Volatility"
                            elif b_val < 0.8:
                                b_col, b_msg = "normal", "Low Volatility"
                            else:
                                b_col, b_msg = "off", "Market Correlated"
                            r1.metric("Beta", f"{b_val:.2f}", delta=b_msg, delta_color=b_col)
                            v_val = metrics['volatility']
                            if v_val < 15:
                                v_col, v_msg = "normal", "Safe" # Green
                            elif v_val > 30:
                                v_col, v_msg = "inverse", "Risky" # Red
                            else:
                                v_col, v_msg = "off", "Moderate"
                            r2.metric("Annual Volatility", f"{v_val:.1f}%", delta=v_msg, delta_color=v_col)
                            s_val = metrics['sharpe']
                            if s_val > 1.0:
                                s_col, s_msg = "normal", "Good Risk-Adjusted Returns"   # Green
                            elif s_val < 0.5:
                                s_col, s_msg = "inverse", "Poor Risk-Adjusted Returns" # Red
                            else:
                                s_col, s_msg = "off", "Average Risk-Adjusted Returns"
                            r3.metric("Sharpe Ratio", f"{s_val:.2f}", delta=s_msg, delta_color=s_col)

                        with st.expander("❓ What do these metrics mean?"):
                            st.markdown("""
                            **Beta (β)**
                            * **What it is:** Measures how much a stock moves compared to the S&P 500.
                            * **The Math:** `Covariance(Stock, Market) / Variance(Market)`
                            * **Interpretation:** 
                                * `1.0`: Moves exactly with the market.
                                * `>1.5`: Very volatile (High Risk/High Reward).
                                * `<0.8`: Defensive stock (Less volatile than the market).
    
                            **Annual Volatility (σ)**
                            * **What it is:** The annualized standard deviation of daily returns. It shows how "bumpy" the ride is.
                            * **The Math:** `StdDev(Daily Returns) * √252` (252 trading days/year).
                            
                            **Sharpe Ratio**
                            * **What it is:** Measures "return per unit of risk." Is the stock worth the stress?
                            * **The Math:** `(Stock Return - Risk Free Rate) / Volatility`
                            * **Interpretation:** A ratio `> 1.0` is generally considered "good" (you are getting paid well for the risk you take).
                            """)

                        # Chart
                        # 1. Get Data (Unpack both stock and market)
                        stock_data, market_data = asset.get_data(start, end)

                        # 2. Normalize Data
                        # comparable even if Stock is $150 and S&P is $4000
                        stock_data['Cumulative Return'] = (stock_data['Close'] / stock_data['Close'].iloc[0] - 1) * 100
                        market_data['Cumulative Return'] = (market_data['Close'] / market_data['Close'].iloc[0] - 1) * 100

                        # 3. Build the "Alpha" Chart
                        st.markdown("##### Performance vs. S&P 500")
                        fig = go.Figure()

                        # A. The Stock
                        # maybe green/red gradient fill later?
                        fig.add_trace(go.Scatter(
                            x=stock_data.index, y=stock_data['Cumulative Return'],
                            mode='lines', name=ticker,
                            line=dict(color='#FF9900', width=2), # Your Amber Brand Color
                            fill='tozeroy', # Fills area under line
                            fillcolor='rgba(255, 153, 0, 0.1)' # Subtle amber glow
                        ))

                        # B. The Benchmark (S&P 500)
                        fig.add_trace(go.Scatter(
                            x=market_data.index, y=market_data['Cumulative Return'],
                            mode='lines', name='S&P 500 (Benchmark)',
                            line=dict(color='#ffffff', width=2, dash='dash') # White dashed line
                        ))

                        # 4. Bloomberg Styling (Updated for % axis)
                        fig.update_layout(
                            height=500,
                            paper_bgcolor='#000000',
                            plot_bgcolor='#000000',
                            margin=dict(t=30, l=0, r=0, b=0),
                            font=dict(color='#ffffff', family="Roboto Mono"),
                            xaxis=dict(showgrid=True, gridcolor='#222', gridwidth=1),
                            yaxis=dict(
                                showgrid=True, gridcolor='#222', gridwidth=1,
                                side='right', # Y-axis on right
                                ticksuffix="%" # Shows numbers as percentages
                            ),
                            legend=dict(x=0, y=1, bgcolor='rgba(0,0,0,0)'),
                            hovermode="x unified"
                        )

                        st.plotly_chart(fig, width="stretch")

                        # Updated Explanation Dropdown
                        with st.expander("❓ How do you read this chart?"):
                            st.markdown("""
                            This chart normalizes both the stock and the S&P 500 to start at 0% on Day 1.
                            
                            * **Amber Line:** The cumulative return of your selected stock.
                            * **White Dashed Line:** The cumulative return of the market (S&P 500).
                            
                            **The "Spread" (Gap) between lines = Alpha.**
                            * If the Amber line is **above** the White line, the stock is generating **excess returns (Alpha)**.
                            * If it is below, it is underperforming the benchmark.
                            """)
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        # Empty State (Waiting for Input)
        with st.container(border=True):
            st.markdown(
                """
                <div style="height: 400px; display: flex; align-items: center; justify-content: center; color: #666;">
                    <div style="text-align: center;">
                        <div style="font-size: 4rem;">📊</div>
                        <p style='color: #444;'>Enter a ticker symbol on the left and click 'Run Analysis' to generate:</p>
                        <ul style='display: inline-block; text-align: left; color: #555;'>
                            <li>Real-time Fundamental Valuation</li>
                            <li>Alpha vs S&P 500 Performance</li>
                            <li>Institutional Risk Metrics (Beta, Sharpe)</li>
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-family: "Roboto Mono", monospace; font-size: 0.8rem;'>
        Alpaca Finance v0.1.4 (Alpha Build) | Data provided by Yahoo Finance.<br>
        Not financial advice. For educational purposes only.<br>
        Created by <a href="https://www.linkedin.com/in/lucasjustinmiller" target="_blank" style="color: #FF9900; text-decoration: none;">Lucas Miller</a>
    </div>
    """,
    unsafe_allow_html=True
)
