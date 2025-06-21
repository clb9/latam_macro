import yfinance as yf

tickers = ['EWZ', 'EWW', 'ECH', 'ARGT']
for ticker in tickers:
    print(f"Testing ticker: {ticker}")
    data = yf.download(ticker, period='1mo')
    print(data.head())
    print("---")