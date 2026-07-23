import yfinance as yf
mgr = yf.data.YfData()
res = mgr.get("https://query2.finance.yahoo.com/v7/finance/quote", params={"symbols": "TCS.NS"}).json()
print(res.get("quoteResponse", {}).get("result", [])[0])
