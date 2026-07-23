import sys
sys.path.insert(0, '/home/at/SchoolProj/Stock-App/.venv/lib/python3.11/site-packages')
import yfinance as yf
import time

tickers = "RELIANCE.NS TCS.NS INFY.NS HDFCBANK.NS"
start = time.time()
data = yf.download(tickers, period="1d", threads=True, progress=False)
print("Time:", time.time() - start)
