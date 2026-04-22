from fastapi import APIRouter
from api.database import execute_query, get_redis
import json
import httpx
import asyncio
from datetime import datetime

router = APIRouter()

# ── helpers ──────────────────────────────────────────────────────────────────

async def _fetch(url: str, timeout: float = 8.0) -> dict | list | None:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url, headers={"User-Agent": "InvestAI/2.0"})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"[exchanges] fetch error {url}: {e}")
        return None


def _fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}"


# ── existing endpoints ────────────────────────────────────────────────────────

@router.get("/moedas")
async def get_moedas():
    redis = get_redis()
    cached = redis.get("moedas:all")
    if cached:
        return json.loads(cached)
    query = "SELECT ticker, preco, variacao_24h FROM cotacoes WHERE fonte='AwesomeAPI' ORDER BY ticker LIMIT 20"
    results = execute_query(query)
    return results or []


@router.get("/binance/portfolio")
async def get_binance_portfolio():
    query = "SELECT * FROM portfolio_binance WHERE valor_brl > 0.01 ORDER BY valor_brl DESC"
    results = execute_query(query)
    total = sum(r['valor_brl'] for r in results) if results else 0
    return {"items": results, "total_brl": total}


@router.get("/onde-investir/{categoria}")
async def onde_investir(categoria: str):
    from core.brokers import BROKERS
    return BROKERS.get(categoria, [])


# ── NEW: cryptos ──────────────────────────────────────────────────────────────

@router.get("/cryptos")
async def get_cryptos():
    """All major cryptos from CoinGecko with BRL/USD prices and 24h change."""
    redis = get_redis()
    cache_key = "exchanges:cryptos"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    ids = (
        "bitcoin,ethereum,binancecoin,solana,ripple,cardano,dogecoin,"
        "avalanche-2,matic-network,polkadot,chainlink,uniswap,shiba-inu,"
        "litecoin,bitcoin-cash"
    )
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids}&vs_currencies=brl,usd&include_24hr_change=true"
    )

    NAME_MAP = {
        "bitcoin": "BTC", "ethereum": "ETH", "binancecoin": "BNB",
        "solana": "SOL", "ripple": "XRP", "cardano": "ADA",
        "dogecoin": "DOGE", "avalanche-2": "AVAX", "matic-network": "MATIC",
        "polkadot": "DOT", "chainlink": "LINK", "uniswap": "UNI",
        "shiba-inu": "SHIB", "litecoin": "LTC", "bitcoin-cash": "BCH",
    }
    DISPLAY_NAMES = {
        "BTC": "Bitcoin", "ETH": "Ethereum", "BNB": "BNB", "SOL": "Solana",
        "XRP": "Ripple", "ADA": "Cardano", "DOGE": "Dogecoin",
        "AVAX": "Avalanche", "MATIC": "Polygon", "DOT": "Polkadot",
        "LINK": "Chainlink", "UNI": "Uniswap", "SHIB": "Shiba Inu",
        "LTC": "Litecoin", "BCH": "Bitcoin Cash",
    }

    data = await _fetch(url)
    result = []
    if data:
        for cg_id, prices in data.items():
            sym = NAME_MAP.get(cg_id, cg_id.upper())
            price_brl = prices.get("brl", 0)
            price_usd = prices.get("usd", 0)
            chg_brl = prices.get("brl_24h_change", 0)
            result.append({
                "symbol": sym,
                "name": DISPLAY_NAMES.get(sym, sym),
                "price_brl": price_brl,
                "price_usd": price_usd,
                "change_24h": round(chg_brl, 2),
                "source": "coingecko",
            })
        # sort by market cap proxy (order in list)
        order = list(NAME_MAP.values())
        result.sort(key=lambda x: order.index(x["symbol"]) if x["symbol"] in order else 99)
    else:
        # Fallback: static data
        result = [
            {"symbol": "BTC", "name": "Bitcoin",  "price_brl": 520000, "price_usd": 94000, "change_24h": 1.2, "source": "static"},
            {"symbol": "ETH", "name": "Ethereum", "price_brl": 16000,  "price_usd": 2900,  "change_24h": 0.8, "source": "static"},
            {"symbol": "BNB", "name": "BNB",       "price_brl": 3200,   "price_usd": 580,   "change_24h": -0.5,"source": "static"},
        ]

    redis.setex(cache_key, 120, json.dumps(result))
    return result


# ── NEW: acoes-b3 ─────────────────────────────────────────────────────────────

@router.get("/acoes-b3")
async def get_acoes_b3():
    """Top B3 stocks via yfinance."""
    redis = get_redis()
    cache_key = "exchanges:acoes_b3"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    tickers = [
        "PETR4.SA","VALE3.SA","ITUB4.SA","BBDC4.SA","ABEV3.SA",
        "WEGE3.SA","RENT3.SA","LREN3.SA","SUZB3.SA","PRIO3.SA",
        "ELET3.SA","BBAS3.SA","CSAN3.SA","CSNA3.SA","AMBP3.SA",
    ]

    result = []
    try:
        import yfinance as yf
        data = yf.download(
            tickers=" ".join(tickers),
            period="2d",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )

        NAMES = {
            "PETR4.SA": "Petrobras PN", "VALE3.SA": "Vale ON", "ITUB4.SA": "Itaú Unibanco PN",
            "BBDC4.SA": "Bradesco PN",  "ABEV3.SA": "Ambev ON", "WEGE3.SA": "WEG ON",
            "RENT3.SA": "Localiza ON",  "LREN3.SA": "Lojas Renner ON", "SUZB3.SA": "Suzano ON",
            "PRIO3.SA": "PetroRio ON",  "ELET3.SA": "Eletrobras ON",  "BBAS3.SA": "Banco do Brasil ON",
            "CSAN3.SA": "Cosan ON",     "CSNA3.SA": "CSN ON",  "AMBP3.SA": "Ambipar ON",
        }

        for tk in tickers:
            try:
                if len(tickers) == 1:
                    closes = data["Close"]
                else:
                    closes = data[tk]["Close"]
                closes = closes.dropna()
                if len(closes) < 1:
                    continue
                price = float(closes.iloc[-1])
                prev  = float(closes.iloc[-2]) if len(closes) >= 2 else price
                change = ((price - prev) / prev * 100) if prev else 0
                sym = tk.replace(".SA", "")
                result.append({
                    "ticker": sym,
                    "name": NAMES.get(tk, sym),
                    "price": round(price, 2),
                    "change_pct": round(change, 2),
                    "source": "yfinance",
                })
            except Exception as e:
                print(f"[yfinance] {tk}: {e}")

    except Exception as e:
        print(f"[acoes-b3] yfinance error: {e}")
        # Fallback static
        result = [
            {"ticker": "PETR4", "name": "Petrobras PN",   "price": 37.42, "change_pct":  1.15, "source": "static"},
            {"ticker": "VALE3", "name": "Vale ON",         "price": 56.80, "change_pct": -0.72, "source": "static"},
            {"ticker": "ITUB4", "name": "Itaú Unibanco PN","price": 32.55, "change_pct":  0.34, "source": "static"},
            {"ticker": "BBDC4", "name": "Bradesco PN",     "price": 14.90, "change_pct": -0.53, "source": "static"},
            {"ticker": "WEGE3", "name": "WEG ON",          "price": 44.20, "change_pct":  0.91, "source": "static"},
            {"ticker": "ELET3", "name": "Eletrobras ON",   "price": 42.60, "change_pct": -0.23, "source": "static"},
            {"ticker": "SUZB3", "name": "Suzano ON",       "price": 47.35, "change_pct": -1.05, "source": "static"},
            {"ticker": "PRIO3", "name": "PetroRio ON",     "price": 43.80, "change_pct":  2.10, "source": "static"},
        ]

    redis.setex(cache_key, 300, json.dumps(result))
    return result


# ── NEW: acoes-int ────────────────────────────────────────────────────────────

@router.get("/acoes-int")
async def get_acoes_int():
    """International stocks via yfinance."""
    redis = get_redis()
    cache_key = "exchanges:acoes_int"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    tickers = ["AAPL","MSFT","GOOGL","AMZN","TSLA","META","NVDA","BRK-B"]
    NAMES = {
        "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com", "TSLA": "Tesla Inc.", "META": "Meta Platforms",
        "NVDA": "NVIDIA Corp.", "BRK-B": "Berkshire Hathaway",
    }

    result = []
    try:
        import yfinance as yf
        for tk in tickers:
            try:
                hist = yf.Ticker(tk).history(period="2d")
                if len(hist) < 1:
                    continue
                price  = float(hist["Close"].iloc[-1])
                prev   = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
                change = ((price - prev) / prev * 100) if prev else 0
                result.append({
                    "ticker": tk,
                    "name": NAMES.get(tk, tk),
                    "price_usd": round(price, 2),
                    "change_pct": round(change, 2),
                    "source": "yfinance",
                })
            except Exception as e:
                print(f"[yfinance int] {tk}: {e}")
    except Exception as e:
        print(f"[acoes-int] error: {e}")
        result = [
            {"ticker": "AAPL", "name": "Apple Inc.",    "price_usd": 224.50, "change_pct":  0.73, "source": "static"},
            {"ticker": "MSFT", "name": "Microsoft Corp.","price_usd": 415.30, "change_pct":  0.45, "source": "static"},
            {"ticker": "NVDA", "name": "NVIDIA Corp.",   "price_usd": 876.20, "change_pct":  1.82, "source": "static"},
            {"ticker": "TSLA", "name": "Tesla Inc.",     "price_usd": 172.40, "change_pct": -2.10, "source": "static"},
        ]

    redis.setex(cache_key, 300, json.dumps(result))
    return result


# ── NEW: renda-fixa ───────────────────────────────────────────────────────────

@router.get("/renda-fixa")
async def get_renda_fixa():
    """Fixed income rates including SELIC from BCB API."""
    redis = get_redis()
    cache_key = "exchanges:renda_fixa"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Try to get SELIC from BCB
    selic_rate = 14.65
    try:
        bcb_data = await _fetch(
            "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json",
            timeout=5.0,
        )
        if bcb_data and len(bcb_data) > 0:
            selic_rate = float(bcb_data[0]["valor"])
    except Exception as e:
        print(f"[bcb] error: {e}")

    cdi = round(selic_rate - 0.10, 2)
    ipca = 4.83  # approximate

    result = [
        {"produto": "SELIC",           "taxa": selic_rate, "periodo": "a.a.", "indexador": "SELIC",      "risco": "baixo",  "liquidez": "D+1",    "source": "bcb"},
        {"produto": "CDI",             "taxa": cdi,        "periodo": "a.a.", "indexador": "CDI",        "risco": "baixo",  "liquidez": "D+0",    "source": "calculado"},
        {"produto": "IPCA",            "taxa": ipca,       "periodo": "a.a.", "indexador": "IPCA",       "risco": "ref",    "liquidez": "-",       "source": "ibge"},
        {"produto": "CDB 100% CDI",    "taxa": round(cdi * 1.00, 2), "periodo": "a.a.", "indexador": "CDI", "risco": "baixo",  "liquidez": "D+1",    "source": "calculado"},
        {"produto": "CDB 103% CDI",    "taxa": round(cdi * 1.03, 2), "periodo": "a.a.", "indexador": "CDI", "risco": "baixo",  "liquidez": "D+0",    "source": "calculado"},
        {"produto": "LCI 94% CDI",     "taxa": round(cdi * 0.94, 2), "periodo": "a.a.", "indexador": "CDI", "risco": "baixo",  "liquidez": "D+30",   "source": "calculado"},
        {"produto": "LCA 90% CDI",     "taxa": round(cdi * 0.90, 2), "periodo": "a.a.", "indexador": "CDI", "risco": "baixo",  "liquidez": "D+90",   "source": "calculado"},
        {"produto": "Tesouro SELIC 2029","taxa": round(selic_rate + 0.10, 2), "periodo": "a.a.", "indexador": "SELIC", "risco": "muito baixo","liquidez": "D+1", "source": "tesouro"},
        {"produto": "Tesouro IPCA 2035","taxa": 7.80,      "periodo": "a.a. + IPCA", "indexador": "IPCA", "risco": "muito baixo","liquidez": "D+1",  "source": "tesouro"},
    ]

    redis.setex(cache_key, 3600, json.dumps(result))
    return result


# ── NEW: moedas-expandido ─────────────────────────────────────────────────────

@router.get("/moedas-expandido")
async def get_moedas_expandido():
    """All major currencies vs BRL via AwesomeAPI."""
    redis = get_redis()
    cache_key = "exchanges:moedas_exp"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    NAMES = {
        "USD": "Dólar Americano", "EUR": "Euro", "GBP": "Libra Esterlina",
        "JPY": "Iene Japonês",    "CAD": "Dólar Canadense", "AUD": "Dólar Australiano",
        "CHF": "Franco Suíço",    "CNY": "Yuan Chinês",
    }

    # Use open.er-api.com (free, no rate limits, no auth)
    er_data = await _fetch("https://open.er-api.com/v6/latest/USD", timeout=6.0)
    result = []

    if er_data and er_data.get("result") == "success":
        rates = er_data.get("rates", {})
        brl_per_usd = rates.get("BRL", 5.0)

        currency_pairs = [
            ("USD", 1.0),
            ("EUR", rates.get("EUR", 0.92)),
            ("GBP", rates.get("GBP", 0.79)),
            ("JPY", rates.get("JPY", 149.0)),
            ("CAD", rates.get("CAD", 1.36)),
            ("AUD", rates.get("AUD", 1.54)),
            ("CHF", rates.get("CHF", 0.88)),
            ("CNY", rates.get("CNY", 7.24)),
        ]

        for sym, rate_vs_usd in currency_pairs:
            if rate_vs_usd == 0:
                continue
            # price in BRL = BRL/USD / (sym/USD)
            price_brl = brl_per_usd / rate_vs_usd
            result.append({
                "par": f"{sym}/BRL",
                "symbol": sym,
                "name": NAMES.get(sym, sym),
                "price": round(price_brl, 4 if price_brl < 1 else 2),
                "change_pct": 0.0,  # er-api doesn't provide change
                "source": "er-api",
            })
    else:
        # Fallback static
        result = [
            {"par": "USD/BRL", "symbol": "USD", "name": "Dólar Americano", "price": 5.05,  "change_pct": 0.0, "source": "static"},
            {"par": "EUR/BRL", "symbol": "EUR", "name": "Euro",             "price": 5.52,  "change_pct": 0.0, "source": "static"},
            {"par": "GBP/BRL", "symbol": "GBP", "name": "Libra Esterlina",  "price": 6.45,  "change_pct": 0.0, "source": "static"},
            {"par": "JPY/BRL", "symbol": "JPY", "name": "Iene Japonês",     "price": 0.034, "change_pct": 0.0, "source": "static"},
            {"par": "CAD/BRL", "symbol": "CAD", "name": "Dólar Canadense",  "price": 3.70,  "change_pct": 0.0, "source": "static"},
            {"par": "AUD/BRL", "symbol": "AUD", "name": "Dólar Australiano","price": 3.30,  "change_pct": 0.0, "source": "static"},
            {"par": "CHF/BRL", "symbol": "CHF", "name": "Franco Suíço",     "price": 5.68,  "change_pct": 0.0, "source": "static"},
            {"par": "CNY/BRL", "symbol": "CNY", "name": "Yuan Chinês",      "price": 0.70,  "change_pct": 0.0, "source": "static"},
        ]

    redis.setex(cache_key, 900, json.dumps(result))  # 15-min cache
    return result


# ── NEW: ticker-tape ──────────────────────────────────────────────────────────

@router.get("/ticker-tape")
async def get_ticker_tape():
    """Combined fast data for the scrolling ticker tape."""
    cryptos_task  = get_cryptos()
    moedas_task   = get_moedas_expandido()
    acoes_task    = get_acoes_b3()

    cryptos, moedas, acoes = await asyncio.gather(
        cryptos_task, moedas_task, acoes_task,
        return_exceptions=True
    )

    items = []

    # B3 Stocks
    if isinstance(acoes, list):
        for a in acoes[:10]:
            items.append({
                "symbol": a["ticker"],
                "price": f"R$ {a['price']:,.2f}",
                "change": a["change_pct"],
            })

    # Moedas
    priority_moedas = ["USD", "EUR", "GBP"]
    if isinstance(moedas, list):
        for m in moedas:
            if m["symbol"] in priority_moedas:
                items.append({
                    "symbol": m["par"],
                    "price": f"R$ {m['price']:,.4f}" if m["price"] < 10 else f"R$ {m['price']:,.2f}",
                    "change": m["change_pct"],
                })

    # Cryptos
    if isinstance(cryptos, list):
        for c in cryptos[:8]:
            p = c["price_brl"]
            fmt = f"R$ {p:,.0f}" if p >= 1000 else f"R$ {p:,.4f}"
            items.append({
                "symbol": c["symbol"],
                "price": fmt,
                "change": c["change_24h"],
            })

    return items
