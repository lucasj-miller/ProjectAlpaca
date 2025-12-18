import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Use python -m streamlit run main.py to run the app

# 1. PAGE SETUP
st.set_page_config(page_title="Alpaca", layout="wide", page_icon="📈")

# 2. CUSTOM CSS (To force the visual style)
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    h1 { font-size: 3rem; font-weight: 700; margin-bottom: 0rem; }
    .subtitle { font-size: 1.2rem; color: #a0a0a0; margin-bottom: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    </style>
""", unsafe_allow_html=True)

# 3. HEADER
col_logo, col_nav = st.columns([1, 4])
with col_logo:
    st.markdown("### 📈 ALPACA") 

st.title("Market Intelligence")
st.markdown('<p class="subtitle">Advanced volatility analysis and AI-driven insights for the modern investor.<br>Analyze securities, track portfolios, and make data-driven decisions.</p>', unsafe_allow_html=True)
st.markdown("---")

# 4. MAIN INTERFACE
col_input, col_result = st.columns([1, 2])

# --- LEFT CARD: INPUTS ---
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

# --- RIGHT CARD: RESULTS ---
with col_result:
    if run_btn and ticker:
        try:
            with st.spinner(f"Analyzing {ticker}..."):
                # Handle dates
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start_d, end_d = date_range
                else:
                    start_d, end_d = default_start, default_end

                # Download Data
                data = yf.download(ticker, start=start_d, end=end_d, progress=False)
                
                if data.empty:
                    st.error(f"No data found for {ticker}.")
                else:
                    # --- Flatten the data ---
                    # yfinance sometimes returns multi-level columns. We simplify them here.
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.droplevel(1)
                    
                    # Get Clean Values
                    current_price = data['Close'].iloc[-1]
                    start_price = data['Close'].iloc[0]
                    
                    # Calculate
                    profit = (current_price - start_price) * shares
                    pct_change = ((current_price - start_price) / start_price) * 100
                    # Calculate daily % returns
                    stock_returns = stock_data['Close'].pct_change().dropna()
                    market_returns = market_data['Close'].pct_change().dropna()
                    
                    # Align data to ensure we compare the exact same dates
                    # (This handles if the stock missed a trading day)
                    combined_data = pd.concat([stock_returns, market_returns], axis=1).dropna()
                    combined_data.columns = ['Stock', 'Market']
                    
                    # Beta Formula: Covariance / Variance
                    covariance = combined_data['Stock'].cov(combined_data['Market'])
                    market_variance = combined_data['Market'].var()
                    beta = covariance / market_variance
                    
                    # Volatility (Annualized Standard Deviation)
                    # We multiply by sqrt(252) because there are ~252 trading days in a year
                    volatility = combined_data['Stock'].std() * np.sqrt(252) * 100
                    
                    # Display Header
                    st.subheader(f"Performance History: {ticker}")
                    
                    # Metrics
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Current Value", f"${(current_price * shares):,.2f}")
                    m2.metric("Net Profit/Loss", f"${profit:,.2f}", delta=f"{pct_change:.2f}%")
                    m3.metric("Close Price", f"${current_price:.2f}")

                    st.markdown("###") # Spacer

                    # Risk Analysis
                    st.markdown("##### Risk Profile")
                    r1, r2, r3 = st.columns(3)
                    
                    # Interpret Beta
                    beta_color = "normal"
                    if beta > 1.5: beta_msg = "High Volatility"
                    elif beta < 0.8: beta_msg = "Low Volatility"
                    else: beta_msg = "Market Correlated"

                    r1.metric("Beta", f"{beta:.2f}", delta=beta_msg, delta_color="off")
                    r2.metric("Annual Volatility", f"{volatility:.1f}%")
                    
                    # Sharpe Ratio (Rough estimate assuming 4% risk free rate)
                    risk_free_rate = 0.04
                    excess_return = (combined_data['Stock'].mean() * 252) - risk_free_rate
                    sharpe = excess_return / (volatility / 100)
                    r3.metric("Sharpe Ratio", f"{sharpe:.2f}")

                    # Chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=data.index, 
                        y=data['Close'], 
                        mode='lines', 
                        name=ticker,
                        line=dict(color='#00D4FF', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(0, 212, 255, 0.1)'
                    ))
                    
                    fig.update_layout(
                        height=400, 
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(t=20, l=0, r=0, b=0),
                        font=dict(color='white'),
                        xaxis=dict(showgrid=False, title=None),
                        yaxis=dict(showgrid=True, gridcolor='#333', title=None)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"An error occurred: {e}")

    else:
        # Empty State
        with st.container(border=True):
            st.markdown(
                """
                <div style="height: 400px; display: flex; align-items: center; justify-content: center; color: #666;">
                    <div style="text-align: center;">
                        <h1>!</h1>
                        <p>Enter a ticker symbol to view performance data</p>
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )