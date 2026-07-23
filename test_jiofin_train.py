import sys
sys.path.insert(0, '/home/at/SchoolProj/Stock-App')
from backend.app.services.prediction_service import PredictionService
from backend.app.services.stock_service import StockService
from backend.app.database.session import session_scope
from backend.app.core.config import get_settings
from backend.app.core.constants import TimeRange

settings = get_settings()
with session_scope(settings) as session:
    from backend.app.providers.chain import default_chain
    chain = default_chain(settings)
    stock_svc = StockService(session, chain)
    
    print("Fetching history...")
    frame, source = stock_svc.get_history_frame("JIOFIN", TimeRange("max"))
    print(f"Got {len(frame)} rows from {source}. Earliest date:", frame["date"].iloc[0])
