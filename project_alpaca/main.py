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
            🦙 Alpaca Finance
        </h1>
        """, 
        unsafe_allow_html=True)

st.markdown(
    """
    <div style='background-color: #111; padding: 15px; border-radius: 5px; border-left: 5px solid #FF9900; margin-bottom: 20px;'>
        <p style='font-size: 1.0rem; color: #ddd; margin: 0; line-height: 1.5;'>
            <b>Equity Research Dashboard:</b> An institutional-grade analytics tool designed for rapid security assessment. 
            This platform integrates real-time <b>Fundamental Valuation</b> (P/E, Market Cap), <b>Quantitative Risk Scoring</b> (Beta, Sharpe Ratio), 
            and <b>Relative Performance Analysis</b> (Alpha vs. S&P 500) to measure excess returns against the benchmark.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# 4. MAIN INTERFACE
col_input, col_result = st.columns([1, 2])

with col_input:
    with st.container(border=True):
        st.subheader("Analyze Security")
        ticker = st.text_input("Ticker Symbol", placeholder="AAPL, TSLA...").upper()
        shares = st.number_input("Number of Shares", min_value=0.01, value=1.0, step=0.01)
        
        default_start = datetime.now() - timedelta(days=365)
        default_end = datetime.now()
        date_range = st.date_input("Analysis Period", (default_start, default_end))
        
        st.markdown("###")
        run_btn = st.button("Run Analysis", type="primary", width="stretch")

# 5. EXECUTION LOGIC
with col_result:
    if run_btn and ticker:
        try:
            with st.spinner(f"Analyzing {ticker}..."):
                # --- INITIALIZE BACKEND CLASS ---
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
                    metrics = asset.calculate_risk_metrics()
                    
                    # --- DISPLAY NEWS (In Left Column) ---
                    with col_input:
                        st.markdown("---")
                        st.subheader("Recent News")
                        news_items = asset.get_news()
                        if news_items:
                            for n in news_items:
                                st.markdown(f"**[{n['title']}]({n['link']})**")
                                st.caption(f"Source: {n['publisher']}")
                                st.markdown("---")
                        else:
                            st.write("No news found.")

                    # --- DISPLAY METRICS ---
                    st.subheader(f"Performance: {ticker}")
                    
                    # Row 1: Money
                    current_price = stock_data['Close'].iloc[-1]
                    start_price = stock_data['Close'].iloc[0]
                    profit = (current_price - start_price) * shares
                    pct_change = ((current_price - start_price) / start_price) * 100

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Current Value", f"${(current_price * shares):,.2f}")
                    m2.metric("Net Profit/Loss", f"${profit:,.2f}", delta=f"{pct_change:.2f}%")
                    m3.metric("Share Price", f"${current_price:.2f}")

                    # Row 2: Fundamentals
                    st.markdown("##### Fundamentals")
                    f1, f2, f3, f4 = st.columns(4)
                    fund_data = asset.get_fundamentals()
                    if fund_data:
                        # 1. Market Cap
                        mktcap = fund_data['market_cap']
                        mktcap_str = "-"
                        if isinstance(mktcap, (int, float)):
                            if mktcap > 1e12:
                                mktcap_str = f"${mktcap / 1e12:.2f}T"
                            elif mktcap > 1e9:
                                mktcap_str = f"${mktcap / 1e9:.2f}B"
                            else:
                                mktcap_str = f"${mktcap / 1e6:.2f}M"
                        f1.metric("Market Cap", mktcap_str)
                        # 2. P/E Ratio
                        pe = fund_data['pe_ratio']
                        if pe:
                            pe_str = f"{pe:.2f}"
                            if pe > 30:
                                pe_msg, pe_col = "Premium", "inverse" # Red
                            elif pe < 15:
                                pe_msg, pe_col = "Value", "normal" # Green
                            else:
                                pe_msg, pe_col = "Fair", "off"
                        else:
                            pe_str, pe_msg, pe_col = "-", None, "off"
                        f2.metric("P/E Ratio", pe_str, delta=pe_msg, delta_color=pe_col)
                        # 3. EPS
                        eps = fund_data['eps']
                        if eps:
                            eps_str = f"${eps:.2f}"
                            if eps > 0:
                                eps_msg, eps_col = "Profitable", "normal" # Green
                            else:
                                eps_msg, eps_col = "Unprofitable", "inverse" # Red
                        else:
                            eps_str, eps_msg, eps_col = "-", None, "off"
                        f3.metric("EPS", eps_str, delta=eps_msg, delta_color=eps_col)
                        # 4. Dividend Yield
                        div = fund_data['dividend_yield']
                        if div:
                            div_str = f"{div*100:.2f}%"
                            div_msg, div_col = "Income", "normal" # Green
                        else:
                            div_str, div_msg, div_col = "-", None, "off"
                        f4.metric("Dividend Yield", div_str, delta=div_msg, delta_color=div_col)

                    # Row 3: Risk Profile
                    st.markdown("##### Risk Profile")
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
                            v_col, v_msg = "normal", "Stable" # Green
                        elif v_val > 30:
                            v_col, v_msg = "inverse", "Volatile" # Red
                        else:
                            v_col, v_msg = "off", "Moderate"
                        r2.metric("Annual Volatility", f"{v_val:.1f}%", delta=v_msg, delta_color=v_col)
                        s_val = metrics['sharpe']
                        if s_val > 1.0:
                            s_col, s_msg = "normal", "Good Risk-Adjusted Returns"   # Green
                        elif s_val < 0.5:
                            s_col, s_msg = "inverse", "Poor Risk-Adjusted Returns" # Red
                        else:
                            s_col, s_msg = "off", "Average"
                        r3.metric("Sharpe Ratio", f"{s_val:.2f}", delta=s_msg, delta_color=s_col)

                    with st.expander("What do these metrics mean?"):
                        st.markdown("""
                        ### Fundamental Metrics (The Business)
                        
                        **Market Cap** 
                        * The total value of the company (Share Price × Total Shares).
                        
                        **P/E Ratio (Price-to-Earnings)** 
                        * How much you pay for $1 of earnings. High (>30) suggests high growth expectations; Low (<15) suggests value.
                        
                        **EPS (Earnings Per Share)** 
                        * The portion of a company's profit allocated to each share. Positive = Profitable.
                        
                        **Dividend Yield** 
                        * The annual percentage return paid to shareholders in dividends.
                        
                        ### Technical Metrics (The Stock)
                        
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
                    with st.expander("How do you read this chart?"):
                        st.markdown("""
                        ### Relative Performance
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
                        <p>Enter a ticker (e.g. AAPL) to view the<br>Equity Research Dashboard</p>
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-family: "Roboto Mono", monospace; font-size: 0.8rem;'>
        Alpaca Finance v0.1.1 (Alpha Build) | Data provided by Yahoo Finance.<br>
        Not financial advice. For educational purposes only.<br>
        Created by <a href="https://www.linkedin.com/in/lucasjustinmiller" target="_blank" style="color: #FF9900; text-decoration: none;">Lucas Miller</a>
    </div>
    """,
    unsafe_allow_html=True
)