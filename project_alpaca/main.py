import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from backend import Asset  # <--- Import your new class

# 1. PAGE CONFIG
st.set_page_config(page_title="Alpaca Finance", layout="wide", page_icon="📈")

# 2. CSS STYLING
st.markdown("""
    <style>
    .stApp { background: linear-gradient(to bottom right, #0e1117, #161b22, #0e1117); }
    .block-container { padding-top: 2rem; }
    h1 { font-size: 3rem; font-weight: 700; margin-bottom: 0rem; }
    .subtitle { font-size: 1.2rem; color: #a0a0a0; margin-bottom: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    </style>
""", unsafe_allow_html=True)

# 3. HEADER
col_logo, col_title = st.columns([0.8, 10]) 

with col_logo:
    # Use HTML to make the emoji big like a logo
    st.markdown("<div style='font-size: 3.5rem; line-height: 1.2;'>📈</div>", unsafe_allow_html=True)

with col_title:
    st.markdown(
        """
        <h1 style='margin-bottom: 0px; margin-top: 0px; padding-top: 10px; font-size: 3rem;'>
            Alpaca Finance
        </h1>
        """, 
        unsafe_allow_html=True
    )

st.markdown('<p class="subtitle">A unified interface for quantitative risk metrics and fundamental news flow.<br>Accelerate due diligence by combining technical indicators with real-time market sentiment.</p>', unsafe_allow_html=True)
st.markdown("---")

# 4. MAIN INTERFACE
col_input, col_result = st.columns([1, 2])

with col_input:
    with st.container(border=True):
        st.subheader("Analyze Security")
        ticker = st.text_input("Ticker Symbol", placeholder="AAPL, TSLA...").upper()
        shares = st.number_input("Number of Shares", min_value=0.01, value=10.0, step=0.1)
        
        default_start = datetime.now() - timedelta(days=365)
        default_end = datetime.now()
        date_range = st.date_input("Analysis Period", (default_start, default_end))
        
        st.markdown("###")
        run_btn = st.button("Run Analysis", type="primary", use_container_width=True)

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
                stock_data = asset.get_data(start, end)
                
                if stock_data.empty:
                    st.error(f"No data found for {ticker}")
                else:
                    metrics = asset.calculate_risk_metrics()
                    
                    # --- DISPLAY NEWS (In Left Column) ---
                    with col_input:
                        st.markdown("---")
                        st.subheader("📢 Recent News")
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

                    # Row 2: Risk Profile
                    st.markdown("##### Risk Profile")
                    r1, r2, r3 = st.columns(3)

                    if metrics:
                        # Color Logic
                        b_val = metrics['beta']
                        if b_val > 1.5: b_col, b_msg = "inverse", "High Volatility"
                        elif b_val < 0.8: b_col, b_msg = "normal", "Low Volatility"
                        else: b_col, b_msg = "off", "Market Correlated"

                        r1.metric("Beta", f"{b_val:.2f}", delta=b_msg, delta_color=b_col)
                        r2.metric("Annual Volatility", f"{metrics['volatility']:.1f}%")
                        r3.metric("Sharpe Ratio", f"{metrics['sharpe']:.2f}")

                    with st.expander("📚 What do these metrics mean?"):
                        st.markdown("""
                        **Beta:** >1.5 is Aggressive, <0.8 is Defensive.
                        **Volatility:** Annualized standard deviation (Risk).
                        **Sharpe:** Return per unit of risk (>1.0 is good).
                        """)

                    # Chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=stock_data.index, y=stock_data['Close'], 
                        mode='lines', name=ticker,
                        line=dict(color='#00D4FF', width=2),
                        fill='tozeroy', fillcolor='rgba(0, 212, 255, 0.1)'
                    ))
                    fig.update_layout(
                        height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(t=20, l=0, r=0, b=0), font=dict(color='white'),
                        xaxis=dict(showgrid=False, title="Date"),
                        yaxis=dict(showgrid=True, gridcolor='#333', title="Price (USD)")
                    )
                    st.plotly_chart(fig, use_container_width=True)
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