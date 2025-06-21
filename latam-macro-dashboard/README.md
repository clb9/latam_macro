# 🌎 Latam Macro Trading Dashboard

A comprehensive Streamlit dashboard for Latin American macro trading analysis, featuring three key models for identifying trading opportunities.

## 🚀 Features

### 1. **FX/Equity Spread Model**
- **Goal**: Spot when equity and FX markets disagree about a country's political or macro outlook
- **Trackers**: 
  - Daily returns on local equity indices (BOVESPA, IPSA, etc.)
  - Daily returns on FX (USDMXN, USDBRL, etc.)
  - Z-score of return divergence over rolling windows
- **Signal**: Large FX-equity divergence indicates mispricing
- **Trade Idea**: Short the "stronger" leg and long the "weaker" leg

### 2. **Momentum Model**
- **Goal**: Quantify risk of surprise election outcomes or political shifts
- **Trackers**:
  - Changes in polling trends (placeholder for future integration)
  - Changes in CDS spreads (placeholder for future integration)
  - Local sentiment from Google Trends, X, or media (placeholder)
- **Signal**: When polling volatility rises and credit spreads widen
- **Trade Idea**: Buy short-term volatility, take pre-election directional bets

### 3. **Event-Driven Gamma Model**
- **Goal**: Exploit underpriced implied volatility ahead of binary events
- **Trackers**:
  - Calendar of political events (elections, IMF votes, court rulings)
  - Current implied volatility (using realized vol as proxy)
  - Historical realized vol to gauge IV cheapness
- **Signal**: Low IV with imminent events triggers gamma opportunity
- **Trade Idea**: Buy straddles/strangles before major political events

## 📊 Dashboard Components

- **Market Overview**: Price performance and daily returns visualization
- **Key Metrics**: Real-time equity and FX metrics with volatility analysis
- **Spread Analysis**: Interactive charts showing return spreads and Z-scores
- **Momentum Indicators**: 5-day momentum and volatility ratios
- **Event Calendar**: Upcoming political events with gamma opportunity analysis
- **Trading Summary**: Consolidated signals from all three models

## 🛠️ Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd latam-macro-dashboard
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the dashboard**:
```bash
streamlit run latam_macro.py
```

## 📈 Supported Countries

- **Brazil**: EWZ (equity), BRL=X (FX), ^BVSP (local equity)
- **Mexico**: EWW (equity), MXN=X (FX), ^MXX (local equity)
- **Chile**: ECH (equity), CLP=X (FX), ^IPSA (local equity)
- **Argentina**: ARGT (equity), ARS=X (FX), ^MERV (local equity)

## ⚙️ Configuration

### Sidebar Controls
- **Country Selection**: Choose from Brazil, Mexico, Chile, or Argentina
- **Lookback Period**: Adjust data period (30-365 days)
- **Volatility Window**: Set rolling window for volatility calculations (5-30 days)

### Signal Thresholds
- **Spread Model**: Z-score > 2 triggers signals
- **Momentum Model**: 5-day momentum thresholds for equity/FX
- **Gamma Model**: Events within 30 days trigger opportunities

## 🔮 Future Enhancements

### Data Sources to Add
1. **CDS Spreads**: Real-time credit default swap data
2. **Polling Data**: Election polling trends and volatility
3. **Options Data**: Implied volatility from options chains
4. **Sentiment Data**: Google Trends, social media sentiment
5. **Economic Indicators**: GDP, inflation, interest rates

### Model Improvements
1. **Machine Learning**: Add ML models for signal generation
2. **Backtesting**: Historical performance analysis
3. **Risk Management**: Position sizing and stop-loss recommendations
4. **Portfolio Optimization**: Multi-country allocation strategies

## 📊 Signal Interpretation

### Spread Model Signals
- **🟢 Bullish**: Long equities, short FX (equities undervalued)
- **🔴 Bearish**: Short equities, long FX (equities overvalued)
- **🟡 Neutral**: No significant divergence

### Momentum Model Signals
- **🟢 Bullish**: Consider long positions
- **🔴 Bearish**: Consider short positions
- **🟡 Neutral**: Mixed signals, wait for clarity

### Gamma Model Signals
- **🟢 Opportunity**: Buy options strategies
- **🟡 Monitor**: Prepare positions
- **🔴 No Opportunity**: Focus on other strategies

## 🚨 Disclaimer

This dashboard is for educational and research purposes only. It does not constitute financial advice. Always conduct your own research and consider consulting with a financial advisor before making investment decisions.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For questions or support, please open an issue in the repository. 