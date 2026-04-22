import os
from binance.spot import Spot
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from api.database import execute_query
import requests

scheduler = BackgroundScheduler()

def fetch_binance_portfolio():
    try:
        api_key = os.getenv("BINANCE_API_KEY", "")
        api_secret = os.getenv("BINANCE_API_SECRET", "")
        
        if not api_key or "SUA_CHAVE" in api_key:
            print("⚠️ Binance API não configurada")
            return
        
        print(f"[{datetime.now()}] Sincronizando Binance...")
        client = Spot(api_key=api_key, api_secret=api_secret)
        account = client.account()
        
        # Buscar USD/BRL
        usd_brl = 4.95
        try:
            url_usd = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
            r = requests.get(url_usd, timeout=5)
            if r.status_code == 200:
                usd_brl = float(r.json()["USDBRL"]["bid"])
        except:
            pass
        
        # Limpar tabela
        execute_query("DELETE FROM portfolio_binance")
        
        for balance in account['balances']:
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked

            if total > 0.0001:
                asset = balance['asset']
                preco_usdt = 1.0 if asset == 'USDT' else 0.0

                if asset != 'USDT':
                    # Handle LD tokens (Locked DeFi staking) - remove LD prefix
                    base_asset = asset[2:] if asset.startswith('LD') and len(asset) > 2 else asset
                    try:
                        ticker = client.ticker_price(symbol=f"{base_asset}USDT")
                        preco_usdt = float(ticker['price'])
                    except:
                        # Try other common pairs
                        for pair_suffix in ['USDT', 'BUSD', 'BTC']:
                            try:
                                ticker = client.ticker_price(symbol=f"{base_asset}{pair_suffix}")
                                preco_usdt = float(ticker['price'])
                                # Convert to USDT if BTC pair
                                if pair_suffix == 'BTC':
                                    btc_price = client.ticker_price(symbol="BTCUSDT")
                                    preco_usdt *= float(btc_price['price'])
                                break
                            except:
                                continue
                
                preco_brl = preco_usdt * usd_brl
                valor_brl = total * preco_brl
                
                query = """INSERT INTO portfolio_binance 
                          (asset, free, locked, total, preco_brl, valor_brl) 
                          VALUES (%s, %s, %s, %s, %s, %s)"""
                execute_query(query, (asset, free, locked, total, preco_brl, valor_brl))
        
        print("✓ Binance sincronizado")
    except Exception as e:
        print(f"✗ Erro Binance: {e}")

def start_scheduler():
    fetch_binance_portfolio()
    scheduler.add_job(fetch_binance_portfolio, 'interval', minutes=10, id='binance_job')
    scheduler.start()
    print("₿ Scheduler Binance iniciado (10min)")
