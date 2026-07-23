import yfinance as yf
hist = yf.Ticker("JIOFIN.NS").history(period="max", end="2026-07-23")
print("Rows:", len(hist))
