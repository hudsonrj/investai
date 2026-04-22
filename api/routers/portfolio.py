from fastapi import APIRouter
from api.database import execute_query
from typing import List, Dict, Any

router = APIRouter()

@router.get("/")
async def get_portfolio():
    """Retorna portfolio completo (Renda Fixa + Ações + Previdência)"""
    query = """
        SELECT id, produto, tipo, instituicao, valor_inicial, valor_atual, 
               rentabilidade_tipo, taxa_anual, liquidez, vencimento, created_at
        FROM portfolio 
        ORDER BY valor_atual DESC
    """
    results = execute_query(query)
    
    if not results:
        return {"items": [], "total": 0, "por_tipo": {}}
    
    # Calcular totais
    total = sum(r['valor_atual'] for r in results)
    
    # Agrupar por tipo
    por_tipo = {}
    for item in results:
        tipo = item['tipo']
        if tipo not in por_tipo:
            por_tipo[tipo] = {'total': 0, 'items': []}
        por_tipo[tipo]['total'] += item['valor_atual']
        por_tipo[tipo]['items'].append(item)
    
    return {
        "items": results,
        "total": float(total),
        "por_tipo": por_tipo
    }

@router.get("/watchlist")
async def get_watchlist():
    """Retorna watchlist com semaphores e análise de risco"""
    import yfinance as yf

    query = """
        SELECT id, ticker, nome, tipo, entrada, alvo, stop,
               quantidade, observacoes, created_at
        FROM watchlist
        ORDER BY ticker
    """
    results = execute_query(query)

    if not results:
        return []

    # Enriquece com preços atuais e semáforos
    watchlist_enriched = []

    for item in results:
        ticker = item['ticker']
        entrada = float(item['entrada'] or 0)
        alvo = float(item['alvo'] or 0)
        stop = float(item['stop'] or 0) if item['stop'] else None

        # Busca preço atual
        preco_atual = None
        variacao_dia = 0
        semaforo = 'amarelo'
        progresso = 0
        ganho_potencial = 0
        risco = 0
        assimetria = 0
        veredicto = 'Neutro'

        try:
            ticker_sa = ticker + '.SA' if not ticker.endswith('.SA') else ticker
            stock = yf.Ticker(ticker_sa)
            hist = stock.history(period='2d')

            if len(hist) > 0:
                preco_atual = hist['Close'].iloc[-1]

                # Variação do dia
                if len(hist) >= 2:
                    preco_anterior = hist['Close'].iloc[-2]
                    variacao_dia = ((preco_atual - preco_anterior) / preco_anterior * 100)

                # Calcula métricas
                ganho_potencial = ((alvo - preco_atual) / preco_atual * 100) if preco_atual > 0 else 0
                risco = ((preco_atual - stop) / preco_atual * 100) if stop and preco_atual > 0 else 10
                assimetria = abs(ganho_potencial / risco) if risco > 0 else 0

                # Progresso (entrada -> alvo)
                if alvo > entrada:
                    progresso = ((preco_atual - entrada) / (alvo - entrada) * 100)
                    progresso = max(0, min(100, progresso))  # Limita entre 0-100%

                # Define semáforo
                if progresso >= 80:
                    semaforo = 'verde'  # Próximo do alvo
                elif stop and preco_atual <= stop * 1.05:  # 5% margem
                    semaforo = 'vermelho'  # Próximo do stop
                elif progresso >= 50:
                    semaforo = 'amarelo-verde'  # Bom progresso
                else:
                    semaforo = 'amarelo'  # Normal

                # Veredicto "Vale o risco?"
                if assimetria >= 2.0:
                    veredicto = 'Favorável'
                elif assimetria >= 1.5:
                    veredicto = 'Aceitável'
                elif assimetria >= 1.0:
                    veredicto = 'Neutro'
                else:
                    veredicto = 'Desfavorável'

        except Exception as e:
            print(f"Erro ao buscar {ticker}: {e}")

        # Monta item enriquecido
        watchlist_enriched.append({
            **dict(item),
            'preco_atual': round(preco_atual, 2) if preco_atual else None,
            'variacao_dia': round(variacao_dia, 2),
            'ganho_potencial': round(ganho_potencial, 2),
            'risco': round(risco, 2),
            'assimetria': round(assimetria, 2),
            'progresso': round(progresso, 2),
            'semaforo': semaforo,
            'veredicto': veredicto
        })

    return watchlist_enriched

@router.get("/resumo")
async def get_resumo():
    """Retorna resumo consolidado do portfolio"""
    # Portfolio principal
    query_portfolio = "SELECT SUM(valor_atual) as total FROM portfolio"
    portfolio_total = execute_query(query_portfolio)
    
    # Binance
    query_binance = "SELECT SUM(valor_brl) as total FROM portfolio_binance WHERE valor_brl > 0.01"
    binance_total = execute_query(query_binance)
    
    portfolio = float(portfolio_total[0]['total']) if portfolio_total and portfolio_total[0]['total'] else 0
    binance = float(binance_total[0]['total']) if binance_total and binance_total[0]['total'] else 0
    total_geral = portfolio + binance
    
    return {
        "portfolio_principal": portfolio,
        "portfolio_binance": binance,
        "total_geral": total_geral,
        "percentual_renda_fixa": (portfolio / total_geral * 100) if total_geral > 0 else 0,
        "percentual_crypto": (binance / total_geral * 100) if total_geral > 0 else 0
    }
