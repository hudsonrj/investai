import yfinance as yf
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from api.database import execute_query
import time

scheduler = BackgroundScheduler()

PRINCIPAIS_ACOES = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA"]

def fetch_acoes_b3():
    try:
        print(f"[{datetime.now()}] Buscando ações B3...")
        for ticker_sa in PRINCIPAIS_ACOES:
            try:
                stock = yf.Ticker(ticker_sa)
                info = stock.info
                hist = stock.history(period="1d")
                if not hist.empty:
                    ticker = ticker_sa.replace(".SA", "")
                    preco = hist['Close'].iloc[-1]
                    variacao = ((hist['Close'].iloc[-1] / hist['Open'].iloc[-1]) - 1) * 100
                    query = "INSERT INTO cotacoes (ticker, fonte, preco, variacao_24h) VALUES (%s, %s, %s, %s)"
                    execute_query(query, (ticker, "B3", float(preco), float(variacao)))
                time.sleep(2)  # Rate limit
            except Exception as e:
                print(f"✗ Erro {ticker_sa}: {e}")
        print("✓ B3 atualizado")
    except Exception as e:
        print(f"✗ Erro geral B3: {e}")

def start_scheduler():
    fetch_acoes_b3()
    scheduler.add_job(fetch_acoes_b3, 'interval', minutes=15, id='b3_job')
    scheduler.start()
    print("📈 Scheduler B3 iniciado (15min)")
