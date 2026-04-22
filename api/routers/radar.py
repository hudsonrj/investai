"""
InvestAI - Radar de Mercado
Mercados globais + Notícias + Análise IA
"""
from fastapi import APIRouter
import yfinance as yf
import feedparser
import os
from groq import Groq
from datetime import datetime, timedelta
import time

router = APIRouter()

# Cache simples
_cache = {}
_cache_times = {}

def cache_get(key, max_age_seconds):
    """Retorna item do cache se ainda válido"""
    if key in _cache and key in _cache_times:
        age = time.time() - _cache_times[key]
        if age < max_age_seconds:
            return _cache[key]
    return None

def cache_set(key, value):
    """Salva item no cache"""
    _cache[key] = value
    _cache_times[key] = time.time()

# Inicializa Groq
groq_client = None
groq_api_key = os.getenv('GROQ_API_KEY')
if groq_api_key:
    groq_client = Groq(api_key=groq_api_key)

@router.get("/indices")
async def get_indices():
    """Alias para mercados (compatibilidade)"""
    return await get_mercados()

@router.get("/mercados")
async def get_mercados():
    """Retorna 10 índices de mercado em tempo real"""
    # Cache de 5 minutos
    cached = cache_get('mercados', 300)
    if cached:
        return cached
    
    indices = [
        {"ticker": "^BVSP", "nome": "IBOVESPA"},
        {"ticker": "^GSPC", "nome": "S&P 500"},
        {"ticker": "^IXIC", "nome": "NASDAQ"},
        {"ticker": "^DJI", "nome": "Dow Jones"},
        {"ticker": "USDBRL=X", "nome": "USD/BRL"},
        {"ticker": "BTC-USD", "nome": "Bitcoin"},
        {"ticker": "GC=F", "nome": "Ouro"},
        {"ticker": "CL=F", "nome": "Petróleo WTI"},
        {"ticker": "BZ=F", "nome": "Petróleo Brent"},
        {"ticker": "^TNX", "nome": "Treasury 10Y"}
    ]
    
    resultado = []
    
    for indice in indices:
        try:
            ticker = yf.Ticker(indice["ticker"])
            hist = ticker.history(period="5d")
            
            if len(hist) >= 2:
                ultimo = hist['Close'].iloc[-1]
                anterior = hist['Close'].iloc[-2]
                variacao = ((ultimo - anterior) / anterior) * 100
                
                resultado.append({
                    "nome": indice["nome"],
                    "valor": f"{ultimo:.2f}",
                    "variacao": round(variacao, 2)
                })
            else:
                resultado.append({
                    "nome": indice["nome"],
                    "valor": "-",
                    "variacao": 0
                })
        except Exception as e:
            print(f"Erro ao buscar {indice['ticker']}: {e}")
            resultado.append({
                "nome": indice["nome"],
                "valor": "-",
                "variacao": 0
            })
    
    cache_set('mercados', resultado)
    return resultado

@router.get("/noticias")
async def get_noticias():
    """Retorna 35 notícias de 7 fontes"""
    # Cache de 15 minutos
    cached = cache_get('noticias', 900)
    if cached:
        return cached
    
    fontes = [
        {
            "nome": "InfoMoney",
            "url": "https://www.infomoney.com.br/feed/",
            "limite": 8
        },
        {
            "nome": "G1 Economia",
            "url": "https://g1.globo.com/economia/index.xml",
            "limite": 5
        },
        {
            "nome": "Folha Mercado",
            "url": "https://feeds.folha.uol.com.br/mercado/rss091.xml",
            "limite": 5
        },
        {
            "nome": "Valor Econômico",
            "url": "https://valor.globo.com/rss/home/",
            "limite": 5
        },
        {
            "nome": "Yahoo Finance",
            "url": "https://finance.yahoo.com/news/rssindex",
            "limite": 5
        },
        {
            "nome": "OilPrice",
            "url": "https://oilprice.com/rss/main",
            "limite": 4
        },
        {
            "nome": "Investing.com",
            "url": "https://br.investing.com/rss/news.rss",
            "limite": 3
        }
    ]
    
    todas_noticias = []
    
    for fonte in fontes:
        try:
            feed = feedparser.parse(fonte["url"])
            for entry in feed.entries[:fonte["limite"]]:
                todas_noticias.append({
                    "fonte": fonte["nome"],
                    "titulo": entry.get('title', 'Sem título'),
                    "descricao": entry.get('summary', '')[:200] if 'summary' in entry else '',
                    "link": entry.get('link', ''),
                    "data": entry.get('published', datetime.now().isoformat())
                })
        except Exception as e:
            print(f"Erro ao buscar notícias de {fonte['nome']}: {e}")
    
    # Ordena por data (mais recentes primeiro)
    todas_noticias.sort(key=lambda x: x['data'], reverse=True)
    
    cache_set('noticias', todas_noticias[:35])
    return todas_noticias[:35]

@router.get("/analise")
async def get_analise():
    """Análise de IA do mercado + notícias"""
    # Cache de 30 minutos
    cached = cache_get('analise', 1800)
    if cached:
        return cached
    
    if not groq_client:
        return {
            "cenario": "neutro",
            "analise": "Análise de IA temporariamente indisponível.",
            "pontos_principais": []
        }
    
    # Busca mercados e notícias
    mercados = await get_mercados()
    noticias = await get_noticias()
    
    # Monta contexto para IA
    contexto_mercados = "\n".join([
        f"- {m['nome']}: {m['valor']} ({'+' if m['variacao'] >= 0 else ''}{m['variacao']}%)"
        for m in mercados[:5]
    ])
    
    contexto_noticias = "\n".join([
        f"- [{n['fonte']}] {n['titulo']}"
        for n in noticias[:10]
    ])
    
    prompt = f"""Analise o mercado financeiro atual com base nos dados abaixo:

MERCADOS:
{contexto_mercados}

NOTÍCIAS RECENTES:
{contexto_noticias}

Forneça uma análise concisa em português brasileiro:
1. Classifique o cenário como: otimista, neutro ou pessimista
2. Resuma a situação em 2-3 linhas
3. Liste 3 pontos principais

Responda em JSON no formato:
{{
  "cenario": "otimista|neutro|pessimista",
  "analise": "texto da análise",
  "pontos_principais": ["ponto 1", "ponto 2", "ponto 3"]
}}
"""
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Você é um analista financeiro expert. Responda sempre em JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        
        resposta_texto = completion.choices[0].message.content
        
        # Tenta extrair JSON
        import json
        import re
        
        # Remove markdown se existir
        resposta_texto = re.sub(r'```json\n?', '', resposta_texto)
        resposta_texto = re.sub(r'```\n?', '', resposta_texto)
        
        resultado = json.loads(resposta_texto)
        
        cache_set('analise', resultado)
        return resultado
        
    except Exception as e:
        print(f"Erro na análise IA: {e}")
        return {
            "cenario": "neutro",
            "analise": "Mercado operando em patamar estável com movimentos laterais. Aguardando catalisadores.",
            "pontos_principais": [
                "Índices principais sem grandes variações",
                "Aguardar definições macroeconômicas",
                "Manter posições defensivas"
            ]
        }
