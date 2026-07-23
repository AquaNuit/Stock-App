import sys
sys.path.insert(0, '/home/at/SchoolProj/Stock-App/.venv/lib/python3.11/site-packages')
import yfinance as yf
ticker = yf.Ticker("JIOFIN.NS")
hist = ticker.history(period="max")
print("Total rows:", len(hist))
if not hist.empty:
    print("Start:", hist.index[0], "End:", hist.index[-1])
