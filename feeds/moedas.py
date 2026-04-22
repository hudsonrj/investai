import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from api.database import execute_query, get_redis
import json

scheduler = BackgroundScheduler()

def fetch_moedas():
    try:
        print(f"[{datetime.now()}] Buscando moedas...")
        url = "https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL,GBP-BRL"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for key, info in {"USDBRL": ("USD", "Dólar"), "EURBRL": ("EUR", "Euro"), "GBPBRL": ("GBP", "Libra")}.items():
                if key in data:
                    ticker, nome = info
                    preco = float(data[key].get("bid", 0))
                    variacao = float(data[key].get("pctChange", 0))
                    query = "INSERT INTO cotacoes (ticker, fonte, preco, variacao_24h) VALUES (%s, %s, %s, %s)"
                    execute_query(query, (ticker, "AwesomeAPI", preco, variacao))
            print("✓ Moedas atualizadas")
    except Exception as e:
        print(f"✗ Erro moedas: {e}")

def start_scheduler():
    fetch_moedas()
    scheduler.add_job(fetch_moedas, 'interval', minutes=5, id='moedas_job')
    scheduler.start()
    print("📊 Scheduler moedas iniciado (5min)")
