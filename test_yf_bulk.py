import sys
sys.path.insert(0, '/home/at/SchoolProj/Stock-App/.venv/lib/python3.11/site-packages')
import yfinance as yf
import time

tickers = " ".join([f"TICKER{i}.NS" for i in range(100)])
start = time.time()
# Note: these are fake tickers so yfinance might skip them, but let's test real ones
from backend.app.data.seed.nse_universe import NIFTY50, BANKNIFTY
tickers = " ".join([f"{s}.NS" for s in NIFTY50 + BANKNIFTY])
data = yf.download(tickers, period="1d", group_by="ticker", auto_adjust=False, progress=False)
print("Time:", time.time() - start)
