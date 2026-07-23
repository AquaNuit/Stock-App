import yfinance as yf
import time

tickers = "RELIANCE.NS TCS.NS INFY.NS HDFCBANK.NS ICICIBANK.NS"
start = time.time()
data = yf.download(tickers, period="1d")
print("Time:", time.time() - start)
print(data)
