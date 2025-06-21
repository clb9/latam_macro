import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from pytrends.request import TrendReq
import time
import requests

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

# Country configuration
countries = {
    'Brazil': {
        'equity': 'EWZ', 
        'currency': 'BRL=X',
        'local_equity': '^BVSP',
        'trends_keywords': ['inflação', 'desemprego', 'Lula']
    },
    'Mexico': {
        'equity': 'EWW', 
        'currency': 'MXN=X',
        'local_equity': '^MXX',
        'trends_keywords': ['inflacion', 'nearshoring', 'amlo']
    },
    'Chile': {
        'equity': 'ECH', 
        'currency': 'CLP=X',
        'local_equity': '^IPSA',
        'trends_keywords': ['inflacion', 'litio', 'Boric']
    },
    'Argentina': {
        'equity': 'ARGT', 
        'currency': 'ARS=X',
        'local_equity': '^MERV',
        'trends_keywords': ['inflacion', 'dolar', 'milei']
    },
    'Peru': {
        'equity': 'EPU',
        'currency': 'PEN=X',
        'local_equity': '^SPBLPGPT',
        'trends_keywords': ['inflacion', 'corrupcion', 'Boluarte']
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

# --- DATA FETCHING ---

@st.cache_data(ttl=3600)
def download_market_data(ticker, period_days):
    session = requests.Session()
    session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    try:
        data = yf.download(ticker, period=f'{period_days}d', progress=False, session=session)
        return data if not data.empty else None
    except Exception:
        return None

@st.cache_data(ttl=3600)
def get_google_trends(keywords, period_days):
    pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25), retries=3, backoff_factor=0.5)
    all_trends_dfs = []
    for keyword in keywords:
        try:
            pytrends.build_payload([keyword], cat=0, timeframe=f'today {period_days}-d', geo='', gprop='')
            trend_df = pytrends.interest_over_time()
            if not trend_df.empty:
                if 'isPartial' in trend_df.columns:
                    trend_df.drop(columns=['isPartial'], inplace=True)
                all_trends_dfs.append(trend_df)
            time.sleep(1)
        except Exception:
            continue
    if not all_trends_dfs:
        return None
    try:
        final_df = pd.concat(all_trends_dfs, axis=1)
        final_df = final_df.loc[:,~final_df.columns.duplicated()]
        return final_df if len(final_df) > 1 else None
    except Exception:
        return None

with st.spinner("Downloading market data..."):
    equity_data = download_market_data(eq_ticker, lookback_days)
    fx_data = download_market_data(fx_ticker, lookback_days)
    local_equity_data = download_market_data(local_eq_ticker, lookback_days)
    trends_data = get_google_trends(country_data['trends_keywords'], lookback_days)

if equity_data is None or fx_data is None:
    st.error("Essential Equity (ETF) or FX data could not be downloaded. Dashboard cannot continue.")
    st.stop()

# --- DATA PROCESSING ---

df = pd.DataFrame(index=equity_data.index)
df['Equity_Price'] = equity_data['Close']
df['FX_Price'] = fx_data['Close']
if local_equity_data is not None and len(local_equity_data) > 5:
    df['Local_Equity_Price'] = local_equity_data['Close']

df.ffill(inplace=True)
df.bfill(inplace=True)
df.dropna(subset=['Equity_Price', 'FX_Price'], inplace=True)

if 'Local_Equity_Price' not in df.columns:
    df['Local_Equity_Price'] = df['Equity_Price'] # Fallback

# --- CALCULATIONS ---

def calculate_returns(prices):
    return prices.pct_change()

def calculate_volatility(returns, window):
    if len(returns.dropna()) < window:
        return pd.Series(np.nan, index=returns.index)
    return returns.rolling(window=window).std() * np.sqrt(252)

def calculate_zscore(series, window=20):
    if len(series.dropna()) < window:
        return pd.Series(np.nan, index=series.index)
    return (series - series.rolling(window=window).mean()) / series.rolling(window=window).std()

df['Equity_Returns'] = calculate_returns(df['Equity_Price'])
df['FX_Returns'] = calculate_returns(df['FX_Price'])
df['Return_Spread'] = df['Equity_Returns'] - df['FX_Returns']
df['Spread_ZScore'] = calculate_zscore(df['Return_Spread'])
df['Equity_Volatility'] = calculate_volatility(df['Equity_Returns'], volatility_window)
df['FX_Volatility'] = calculate_volatility(df['FX_Returns'], volatility_window)

df_cleaned = df.dropna()

# --- UI LAYOUT ---

st.markdown(f'<h2 class="model-header">📈 Market Overview - {selected_country}</h2>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    if not df_cleaned.empty:
        fig_market = make_subplots(specs=[[{"secondary_y": True}]])
        fig_market.add_trace(go.Scatter(x=df_cleaned.index, y=df_cleaned['Equity_Price'], name='Equity ETF', line=dict(color='blue')), secondary_y=False)
        fig_market.add_trace(go.Scatter(x=df_cleaned.index, y=df_cleaned['FX_Price'], name='FX Rate', line=dict(color='red')), secondary_y=True)
        fig_market.update_layout(
            height=500, title_text=f'Price Performance', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_market.update_yaxes(title_text="Equity Price (USD)", secondary_y=False)
        fig_market.update_yaxes(title_text="FX Rate (vs. USD)", secondary_y=True)
        st.plotly_chart(fig_market, use_container_width=True)
    else:
        st.warning("Not enough data for price chart.")

with col2:
    st.markdown('<h3 class="model-header">📊 Key Metrics</h3>', unsafe_allow_html=True)
    if not df_cleaned.empty:
        st.metric("Equity ETF", f"${df_cleaned['Equity_Price'].iloc[-1]:.2f}")
        st.metric("FX Rate", f"{df_cleaned['FX_Price'].iloc[-1]:.4f}")
        st.metric("Equity Volatility", f"{df_cleaned['Equity_Volatility'].iloc[-1]*100:.1f}%")
        st.metric("FX Volatility", f"{df_cleaned['FX_Volatility'].iloc[-1]*100:.1f}%")
    else:
        st.info("No metrics to display.")

# Models
st.markdown('<hr>', unsafe_allow_html=True)
mcol1, mcol2, mcol3 = st.columns(3)

with mcol1:
    st.markdown('<h3 class="model-header">🔄 FX/Equity Spread</h3>', unsafe_allow_html=True)
    if not df_cleaned.empty:
        current_zscore = df_cleaned['Spread_ZScore'].iloc[-1]
        st.metric("Spread Z-Score", f"{current_zscore:.2f}")
        if abs(current_zscore) > 2:
            signal_class, signal_text = ("signal-bearish", "Short equities, long FX") if current_zscore > 2 else ("signal-bullish", "Long equities, short FX")
        else:
            signal_class, signal_text = "signal-neutral", "No divergence"
    else:
        st.metric("Spread Z-Score", "N/A")
        signal_class, signal_text = "signal-neutral", "Not enough data"
    st.markdown(f'<div class="signal-box {signal_class}">{signal_text}</div>', unsafe_allow_html=True)

with mcol2:
    st.markdown('<h3 class="model-header">📊 Sentiment</h3>', unsafe_allow_html=True)
    if trends_data is not None and not trends_data.empty:
        trends_data['Concern_Index'] = trends_data.mean(axis=1)
        trends_data['Concern_ZScore'] = calculate_zscore(trends_data['Concern_Index'])
        if not trends_data['Concern_ZScore'].dropna().empty:
            current_concern_zscore = trends_data['Concern_ZScore'].iloc[-1]
            st.metric("Public Concern Z-Score", f"{current_concern_zscore:.2f}")
            signal_class, signal_text = ("signal-bearish", "High Public Concern") if current_concern_zscore > 1.5 else ("signal-neutral", "Normal Concern")
        else:
            st.metric("Public Concern Z-Score", "N/A")
            signal_class, signal_text = "signal-neutral", "Not enough data"
    else:
        st.metric("Public Concern Z-Score", "N/A")
        signal_class, signal_text = "signal-neutral", "Could not load data"
    st.markdown(f'<div class="signal-box {signal_class}">{signal_text}</div>', unsafe_allow_html=True)

with mcol3:
    st.markdown('<h3 class="model-header">⚡️ Performance</h3>', unsafe_allow_html=True)
    if len(df_cleaned) > 5:
        five_day_return = (df_cleaned['Equity_Price'].iloc[-1] / df_cleaned['Equity_Price'].iloc[-6] - 1) * 100
        st.metric("Equity Momentum (5d)", f"{five_day_return:+.2f}%")
        if five_day_return > 2:
            signal_class, signal_text = "signal-bullish", "Positive Momentum"
        elif five_day_return < -2:
            signal_class, signal_text = "signal-bearish", "Negative Momentum"
        else:
            signal_class, signal_text = "signal-neutral", "Neutral"
    else:
        st.metric("Equity Momentum (5d)", "N/A")
        signal_class, signal_text = "signal-neutral", "Not enough data"
    st.markdown(f'<div class="signal-box {signal_class}">{signal_text}</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"*Data from Yahoo Finance & Google Trends. Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")