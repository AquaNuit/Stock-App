import sys
import time
sys.path.insert(0, '/home/at/SchoolProj/Stock-App')
from backend.app.services.market_data import MarketDataService
from backend.app.providers.chain import default_chain
from backend.app.cache.manager import CacheManager
from backend.app.core.config import get_settings

settings = get_settings()
cache = CacheManager(settings)
chain = default_chain(settings, cache)

svc = MarketDataService(chain, cache)
start = time.time()
print("Fetching overview...")
res = svc.overview()
print("Time:", time.time() - start)
print(f"Advancers: {res.advancers}, Decliners: {res.decliners}")
