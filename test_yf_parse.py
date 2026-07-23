import sys
sys.path.insert(0, '/home/at/SchoolProj/Stock-App/.venv/lib/python3.11/site-packages')
import yfinance as yf
import pandas as pd

def parse_quotes(symbols):
    yf_symbols = [f"{s}.NS" for s in symbols]
    data = yf.download(" ".join(yf_symbols), period="5d", group_by="ticker", auto_adjust=False, progress=False)
    res = {}
    for i, sym in enumerate(symbols):
        yf_sym = yf_symbols[i]
        try:
            if len(symbols) == 1:
                df = data
            else:
                if yf_sym not in data.columns.levels[0]:
                    continue
                df = data[yf_sym]
            df = df.dropna(subset=["Close"])
            if df.empty: continue
            res[sym] = float(df["Close"].iloc[-1])
        except Exception as e:
            print(f"Error {sym}: {e}")
    return res

print(parse_quotes(["RELIANCE", "TCS", "INVALID123"]))
print(parse_quotes(["RELIANCE"]))
