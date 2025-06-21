import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Latam Macro Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .model-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .signal-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .signal-bullish {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .signal-bearish {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .signal-neutral {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🌎 Latam Macro Trading Dashboard</h1>', unsafe_allow_html=True)

# Country configuration with more comprehensive data
countries = {
    'Brazil': {
        'equity': 'EWZ', 
        'currency': 'BRL=X',
        'local_equity': '^BVSP',
        'cds_ticker': 'BRAZIL_CDS',  # Placeholder
        'elections': ['2024-10-06'],  # Example election dates
        'color': '#009c3b'
    },
    'Mexico': {
        'equity': 'EWW', 
        'currency': 'MXN=X',
        'local_equity': '^MXX',
        'cds_ticker': 'MEXICO_CDS',
        'elections': ['2024-06-02'],
        'color': '#006847'
    },
    'Chile': {
        'equity': 'ECH', 
        'currency': 'CLP=X',
        'local_equity': '^IPSA',
        'cds_ticker': 'CHILE_CDS',
        'elections': ['2025-11-23'],
        'color': '#d52b1e'
    },
    'Argentina': {
        'equity': 'ARGT', 
        'currency': 'ARS=X',
        'local_equity': '^MERV',
        'cds_ticker': 'ARGENTINA_CDS',
        'elections': ['2025-10-26'],
        'color': '#75aadb'
    }
}

# Sidebar configuration
st.sidebar.markdown("## 📍 Configuration")
selected_country = st.sidebar.selectbox("Choose a country", list(countries.keys()))
lookback_days = st.sidebar.slider("Lookback period (days)", 30, 365, 90)
volatility_window = st.sidebar.slider("Volatility calculation window", 5, 30, 10)

# Get country data
country_data = countries[selected_country]
eq_ticker = country_data['equity']
fx_ticker = country_data['currency']
local_eq_ticker = country_data['local_equity']

# Download data with error handling
@st.cache_data(ttl=3600)  # Cache for 1 hour
def download_market_data(ticker, period_days):
    try:
        data = yf.download(ticker, period=f'{period_days}d', progress=False)
        if data.empty:
            return None
        return data
    except Exception as e:
        st.error(f"Failed to download {ticker}: {e}")
        return None

# Download all data
with st.spinner("Downloading market data..."):
    equity_data = download_market_data(eq_ticker, lookback_days)
    fx_data = download_market_data(fx_ticker, lookback_days)
    local_equity_data = download_market_data(local_eq_ticker, lookback_days)

# Debug information
st.sidebar.markdown("### 🔍 Debug Info")
st.sidebar.write(f"Equity ticker: {eq_ticker}")
st.sidebar.write(f"FX ticker: {fx_ticker}")
st.sidebar.write(f"Local equity ticker: {local_eq_ticker}")

if equity_data is not None:
    st.sidebar.write(f"Equity data shape: {equity_data.shape}")
else:
    st.sidebar.error("Equity data download failed")

if fx_data is not None:
    st.sidebar.write(f"FX data shape: {fx_data.shape}")
else:
    st.sidebar.error("FX data download failed")

if local_equity_data is not None:
    st.sidebar.write(f"Local equity data shape: {local_equity_data.shape}")
else:
    st.sidebar.warning("Local equity data download failed or ticker not found.")

if equity_data is None or equity_data.empty or fx_data is None or fx_data.empty:
    st.error("Essential Equity (ETF) or FX data could not be downloaded. Dashboard cannot continue.")
    st.stop()

# Data preprocessing
def calculate_returns(prices):
    return prices.pct_change().dropna()

def calculate_volatility(returns, window):
    return returns.rolling(window=window).std() * np.sqrt(252)

def calculate_zscore(series, window=20):
    return (series - series.rolling(window=window).mean()) / series.rolling(window=window).std()

# Process data
# First, perform a hard check for the essential data.
if equity_data is None or equity_data.empty:
    st.error("Essential Equity (ETF) data could not be downloaded. Dashboard cannot continue.")
    st.stop()

# 1. Establish the equity index as the master index for our DataFrame.
df = pd.DataFrame(index=equity_data.index)

# 2. Add data column by column. This is the most robust method.
#    Assigning a Series to a DataFrame column automatically aligns by index.
df['Equity_Price'] = equity_data['Close']

if fx_data is not None and not fx_data.empty:
    df['FX_Price'] = fx_data['Close']

# Only add local equity data if it has a meaningful number of data points.
MIN_DATA_POINTS = 5
if local_equity_data is not None and len(local_equity_data) >= MIN_DATA_POINTS:
    df['Local_Equity_Price'] = local_equity_data['Close']

# 3. Now that the DataFrame is assembled, fill all missing values.
#    ffill() propagates the last valid observation forward.
#    bfill() handles any NaNs that may be left at the very beginning.
df.ffill(inplace=True)
df.bfill(inplace=True)

# 4. Defensively ensure required columns exist and are filled.
if 'FX_Price' not in df.columns:
    st.error("FX data could not be loaded or aligned. Cannot proceed with analysis.")
    st.stop()
    
if 'Local_Equity_Price' not in df.columns:
    df['Local_Equity_Price'] = df['Equity_Price'] # Fallback for optional data

# 5. Drop any rows that still have NaNs (this can happen if a ticker's
#    entire date range is outside the master index).
df.dropna(inplace=True)

# 6. Final check to ensure we have a usable DataFrame.
if df.empty:
    st.error("No overlapping data could be constructed for the selected assets.")
    st.stop()

# 7. Calculate returns and other metrics. This is now guaranteed to be safe.
df['Equity_Returns'] = calculate_returns(df['Equity_Price'])
df['FX_Returns'] = calculate_returns(df['FX_Price'])
df['Local_Equity_Returns'] = calculate_returns(df['Local_Equity_Price'])

df.dropna(inplace=True)

df['Equity_Volatility'] = calculate_volatility(df['Equity_Returns'], volatility_window)
df['FX_Volatility'] = calculate_volatility(df['FX_Returns'], volatility_window)
df['Return_Spread'] = df['Equity_Returns'] - df['FX_Returns']
df['Spread_ZScore'] = calculate_zscore(df['Return_Spread'])

# Drop NaNs introduced by rolling calculations.
df.dropna(inplace=True)

if df.empty:
    st.error("Not enough data to compute metrics after cleaning. Please extend the lookback period.")
    st.stop()

# Main dashboard layout
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f'<h2 class="model-header">📈 Market Overview - {selected_country}</h2>', unsafe_allow_html=True)
    
    # Price chart
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Price Performance', 'Daily Returns'),
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3]
    )
    
    # Price subplot
    fig.add_trace(
        go.Scatter(x=df.index, y=df['Equity_Price'], name='Equity ETF', line=dict(color='blue')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['FX_Price'], name='FX Rate', line=dict(color='red'), yaxis='y2'),
        row=1, col=1
    )
    
    # Returns subplot
    fig.add_trace(
        go.Scatter(x=df.index, y=df['Equity_Returns'], name='Equity Returns', line=dict(color='blue')),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['FX_Returns'], name='FX Returns', line=dict(color='red')),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        title=f'{selected_country} Market Performance (Last {lookback_days} days)',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown('<h3 class="model-header">📊 Key Metrics</h3>', unsafe_allow_html=True)
    
    # Current metrics
    current_equity = df['Equity_Price'].iloc[-1]
    current_fx = df['FX_Price'].iloc[-1]
    equity_change = ((current_equity / df['Equity_Price'].iloc[-2]) - 1) * 100
    fx_change = ((current_fx / df['FX_Price'].iloc[-2]) - 1) * 100
    
    st.metric("Equity ETF", f"${current_equity:.2f}", f"{equity_change:+.2f}%")
    st.metric("FX Rate", f"{current_fx:.4f}", f"{fx_change:+.2f}%")
    
    # Volatility metrics
    current_equity_vol = df['Equity_Volatility'].iloc[-1] * 100
    current_fx_vol = df['FX_Volatility'].iloc[-1] * 100
    
    st.metric("Equity Volatility", f"{current_equity_vol:.1f}%")
    st.metric("FX Volatility", f"{current_fx_vol:.1f}%")

# Model 1: FX/Equity Spread Model
st.markdown('<h2 class="model-header">🔄 FX/Equity Spread Model</h2>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    # Spread analysis chart
    fig_spread = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Return Spread (Equity - FX)', 'Spread Z-Score'),
        vertical_spacing=0.1
    )
    
    fig_spread.add_trace(
        go.Scatter(x=df.index, y=df['Return_Spread'], name='Return Spread', line=dict(color='purple')),
        row=1, col=1
    )
    fig_spread.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
    
    fig_spread.add_trace(
        go.Scatter(x=df.index, y=df['Spread_ZScore'], name='Z-Score', line=dict(color='orange')),
        row=2, col=1
    )
    fig_spread.add_hline(y=2, line_dash="dash", line_color="red", row=2, col=1)
    fig_spread.add_hline(y=-2, line_dash="dash", line_color="red", row=2, col=1)
    fig_spread.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
    
    fig_spread.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig_spread, use_container_width=True)

with col2:
    # Spread model signals
    current_spread = df['Return_Spread'].iloc[-1]
    current_zscore = df['Spread_ZScore'].iloc[-1]
    
    st.markdown('<h4>📊 Spread Analysis</h4>', unsafe_allow_html=True)
    st.metric("Current Spread", f"{current_spread:.4f}")
    st.metric("Z-Score", f"{current_zscore:.2f}")
    
    # Generate spread signal
    if abs(current_zscore) > 2:
        if current_zscore > 2:
            signal_class = "signal-bearish"
            signal_text = "🔴 BEARISH SPREAD SIGNAL"
            trade_idea = "Short equities, long FX (equities overvalued vs FX)"
        else:
            signal_class = "signal-bullish"
            signal_text = "🟢 BULLISH SPREAD SIGNAL"
            trade_idea = "Long equities, short FX (equities undervalued vs FX)"
    else:
        signal_class = "signal-neutral"
        signal_text = "🟡 NEUTRAL SPREAD"
        trade_idea = "No significant divergence detected"
    
    st.markdown(f'<div class="signal-box {signal_class}">{signal_text}</div>', unsafe_allow_html=True)
    st.info(f"**Trade Idea:** {trade_idea}")

# Model 2: Momentum Model (Framework)
st.markdown('<h2 class="model-header">📊 Momentum Model</h2>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<h4>📈 Momentum Indicators</h4>', unsafe_allow_html=True)
    
    # Calculate momentum indicators
    df['Equity_Momentum'] = df['Equity_Price'].pct_change(5)  # 5-day momentum
    df['FX_Momentum'] = df['FX_Price'].pct_change(5)
    df['Volatility_Ratio'] = df['Equity_Volatility'] / df['FX_Volatility']
    
    # Current momentum values
    current_equity_momentum = df['Equity_Momentum'].iloc[-1] * 100
    current_fx_momentum = df['FX_Momentum'].iloc[-1] * 100
    current_vol_ratio = df['Volatility_Ratio'].iloc[-1]
    
    st.metric("Equity Momentum (5d)", f"{current_equity_momentum:+.2f}%")
    st.metric("FX Momentum (5d)", f"{current_fx_momentum:+.2f}%")
    st.metric("Volatility Ratio", f"{current_vol_ratio:.2f}")
    
    # Placeholder for polling/CDS data
    st.markdown('<h4>🗳️ Political Risk Indicators</h4>', unsafe_allow_html=True)
    st.warning("⚠️ Polling and CDS data integration pending")
    st.info("Future features: Polling trends, CDS spreads, Google Trends sentiment")

with col2:
    st.markdown('<h4>🎯 Momentum Signals</h4>', unsafe_allow_html=True)
    
    # Simple momentum signal logic
    momentum_score = 0
    if current_equity_momentum > 2:
        momentum_score += 1
    elif current_equity_momentum < -2:
        momentum_score -= 1
    
    if current_fx_momentum > 1:
        momentum_score += 1
    elif current_fx_momentum < -1:
        momentum_score -= 1
    
    if momentum_score > 0:
        signal_class = "signal-bullish"
        signal_text = "🟢 BULLISH MOMENTUM"
        trade_idea = "Consider long positions, momentum favors upside"
    elif momentum_score < 0:
        signal_class = "signal-bearish"
        signal_text = "🔴 BEARISH MOMENTUM"
        trade_idea = "Consider short positions, momentum favors downside"
    else:
        signal_class = "signal-neutral"
        signal_text = "🟡 NEUTRAL MOMENTUM"
        trade_idea = "Mixed signals, wait for clearer direction"
    
    st.markdown(f'<div class="signal-box {signal_class}">{signal_text}</div>', unsafe_allow_html=True)
    st.info(f"**Trade Idea:** {trade_idea}")

# Model 3: Event-Driven Gamma Model
st.markdown('<h2 class="model-header">🎲 Event-Driven Gamma Model</h2>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    # Event calendar and volatility analysis
    st.markdown('<h4>📅 Upcoming Political Events</h4>', unsafe_allow_html=True)
    
    # Get upcoming events for selected country
    upcoming_events = country_data.get('elections', [])
    
    if upcoming_events:
        event_df = pd.DataFrame({
            'Event': ['Election'] * len(upcoming_events),
            'Date': upcoming_events,
            'Days Until': [(datetime.strptime(date, '%Y-%m-%d') - datetime.now()).days for date in upcoming_events]
        })
        
        # Filter for upcoming events only
        event_df = event_df[event_df['Days Until'] > 0].sort_values('Days Until')
        
        if not event_df.empty:
            st.dataframe(event_df, use_container_width=True)
            
            # Gamma opportunity analysis
            nearest_event_days = event_df['Days Until'].iloc[0]
            
            if nearest_event_days <= 30:
                gamma_signal = "🟢 GAMMA OPPORTUNITY"
                gamma_class = "signal-bullish"
                gamma_idea = f"Buy straddles/strangles - {nearest_event_days} days until event"
            elif nearest_event_days <= 90:
                gamma_signal = "🟡 MONITOR GAMMA"
                gamma_class = "signal-neutral"
                gamma_idea = f"Prepare gamma positions - {nearest_event_days} days until event"
            else:
                gamma_signal = "🔴 NO GAMMA OPPORTUNITY"
                gamma_class = "signal-bearish"
                gamma_idea = "Too far from events, focus on other strategies"
        else:
            st.info("No upcoming events in the next 365 days")
            gamma_signal = "🔴 NO GAMMA OPPORTUNITY"
            gamma_class = "signal-bearish"
            gamma_idea = "No upcoming events detected"
    else:
        st.info("No events configured for this country")
        gamma_signal = "🔴 NO GAMMA OPPORTUNITY"
        gamma_class = "signal-bearish"
        gamma_idea = "No events configured"

with col2:
    st.markdown('<h4>🎯 Gamma Signals</h4>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="signal-box {gamma_class}">{gamma_signal}</div>', unsafe_allow_html=True)
    st.info(f"**Trade Idea:** {gamma_idea}")
    
    # Volatility analysis for gamma
    st.markdown('<h4>📊 Volatility Analysis</h4>', unsafe_allow_html=True)
    
    # Calculate implied volatility proxy (using realized vol as approximation)
    avg_equity_vol = df['Equity_Volatility'].mean() * 100
    current_equity_vol = df['Equity_Volatility'].iloc[-1] * 100
    vol_percentile = (df['Equity_Volatility'] < df['Equity_Volatility'].iloc[-1]).mean() * 100
    
    st.metric("Avg Equity Vol", f"{avg_equity_vol:.1f}%")
    st.metric("Current Vol", f"{current_equity_vol:.1f}%")
    st.metric("Vol Percentile", f"{vol_percentile:.0f}%")

# Summary and recommendations
st.markdown('<h2 class="model-header">📋 Trading Summary</h2>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<h4>🔄 Spread Model</h4>', unsafe_allow_html=True)
    if abs(current_zscore) > 2:
        if current_zscore > 2:
            st.error("Short equities, long FX")
        else:
            st.success("Long equities, short FX")
    else:
        st.info("No spread signal")

with col2:
    st.markdown('<h4>📊 Momentum Model</h4>', unsafe_allow_html=True)
    if momentum_score > 0:
        st.success("Bullish momentum")
    elif momentum_score < 0:
        st.error("Bearish momentum")
    else:
        st.info("Neutral momentum")

with col3:
    st.markdown('<h4>🎲 Gamma Model</h4>', unsafe_allow_html=True)
    if "OPPORTUNITY" in gamma_signal:
        st.success("Gamma opportunity detected")
    else:
        st.info("No gamma opportunity")

# Footer
st.markdown("---")
st.markdown("*Data source: Yahoo Finance | Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "*") 