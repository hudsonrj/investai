from fastapi import APIRouter
from api.database import execute_query
import yfinance as yf

router = APIRouter()

@router.get("/portfolio")
async def get_portfolio():
    query = "SELECT * FROM portfolio ORDER BY tipo, produto"
    return execute_query(query)

@router.get("/watchlist")
async def get_watchlist():
    query = "SELECT * FROM watchlist ORDER BY created_at DESC"
    return execute_query(query)

@router.get("/{ticker}")
async def get_historico(ticker: str, periodo: str = "1y"):
    try:
        stock = yf.Ticker(ticker + ".SA" if not "." in ticker else ticker)
        hist = stock.history(period=periodo)
        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })
        return {"ticker": ticker, "periodo": periodo, "data": data}
    except:
        return {"ticker": ticker, "data": []}
