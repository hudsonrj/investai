"""
InvestAI - Sugestões Router
Endpoints for AI-generated suggestions and action cards
"""
from fastapi import APIRouter
from api.database import execute_query
from agents.suggestion_engine import SuggestionEngine
from agents.orchestrator import Orchestrator

router = APIRouter()

# Initialize agents
suggestion_engine = SuggestionEngine()
orchestrator = Orchestrator()

@router.get("/")
async def get_sugestoes():
    """Retorna sugestões gerais da IA"""
    query = "SELECT * FROM sugestoes WHERE status='nova' ORDER BY created_at DESC LIMIT 10"
    sugestoes = execute_query(query)
    return sugestoes or []

@router.get("/cards")
async def get_action_cards():
    """Retorna action cards ativos (proativos)"""
    try:
        # Busca cards do banco (gerados pelo suggestion engine)
        query = """
            SELECT id, tipo, titulo, descricao, ticker, preco_atual, preco_alvo,
                   ganho_potencial, risco, justificativa, acoes_sugeridas, prioridade,
                   created_at
            FROM action_cards
            WHERE status = 'ativa'
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY prioridade ASC, created_at DESC
            LIMIT 6
        """
        cards = execute_query(query)

        if not cards:
            # Se não há cards no banco, gera novos
            cards = suggestion_engine.gerar_action_cards()

        # Formata acoes_sugeridas (JSON parse se necessário)
        import json
        for card in cards:
            if isinstance(card.get('acoes_sugeridas'), str):
                try:
                    card['acoes_sugeridas'] = json.loads(card['acoes_sugeridas'])
                except:
                    card['acoes_sugeridas'] = []

        return cards

    except Exception as e:
        print(f"Erro ao buscar action cards: {e}")
        return []

@router.get("/briefing")
async def get_briefing():
    """Retorna último briefing diário"""
    query = "SELECT * FROM briefings ORDER BY timestamp DESC LIMIT 1"
    result = execute_query(query, fetch_one=True)

    if result:
        return result

    return {
        "titulo": "Sem briefing disponível",
        "conteudo": "Nenhum briefing foi gerado hoje. Aguarde o próximo horário (09:00, 13:00 ou 21:00 UTC).",
        "timestamp": None
    }

@router.post("/gerar-briefing")
async def gerar_briefing():
    """Gera um novo briefing sob demanda"""
    try:
        briefing = suggestion_engine.gerar_briefing_diario()
        return briefing
    except Exception as e:
        return {
            "erro": str(e),
            "titulo": "Erro ao gerar briefing",
            "conteudo": "Ocorreu um erro ao gerar o briefing. Tente novamente."
        }

@router.post("/atualizar-cards")
async def atualizar_cards():
    """Atualiza action cards sob demanda"""
    try:
        cards = suggestion_engine.gerar_action_cards()
        return {
            "success": True,
            "cards_gerados": len(cards),
            "cards": cards
        }
    except Exception as e:
        return {
            "success": False,
            "erro": str(e)
        }

@router.get("/carteira-recomendada")
async def get_carteira_recomendada():
    """Retorna carteira recomendada pela IA"""
    try:
        # Busca última recomendação válida
        query = """
            SELECT * FROM carteira_recomendada
            WHERE valido_ate > NOW()
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = execute_query(query, fetch_one=True)

        if result:
            import json
            # Parse JSON fields
            result['alocacao'] = json.loads(result['alocacao']) if isinstance(result['alocacao'], str) else result['alocacao']
            result['ativos_sugeridos'] = json.loads(result['ativos_sugeridos']) if isinstance(result.get('ativos_sugeridos'), str) else result.get('ativos_sugeridos')
            result['rebalanceamento_necessario'] = json.loads(result['rebalanceamento_necessario']) if isinstance(result.get('rebalanceamento_necessario'), str) else result.get('rebalanceamento_necessario')
            return result

        # Se não há recomendação, gera uma baseada no perfil moderado
        from ml.cenarios import CenariosML

        cenarios_ml = CenariosML()

        # Busca valor total do portfolio
        query_portfolio = "SELECT SUM(valor_atual) as total FROM portfolio"
        portfolio_result = execute_query(query_portfolio, fetch_one=True)
        total = float(portfolio_result['total'] or 0) if portfolio_result else 395000

        # Busca crypto
        query_crypto = "SELECT SUM(valor_brl) as total FROM portfolio_binance"
        crypto_result = execute_query(query_crypto, fetch_one=True)
        crypto_total = float(crypto_result['total'] or 0) if crypto_result else 0

        valor_total = total + crypto_total

        # Gera cenários
        cenarios = cenarios_ml.gerar_cenarios({"total": valor_total})

        # Retorna cenário moderado
        moderado = next((c for c in cenarios if c['nome'] == 'Moderado'), cenarios[0])

        return {
            "perfil": "Moderado",
            "alocacao": moderado['alocacao'],
            "valor_total_sugerido": valor_total,
            "justificativa": "Carteira equilibrada entre segurança (60% RF) e crescimento (40% RV/Crypto)",
            "ativos_sugeridos": {
                "rf": ["CDB BTG 103% CDI", "Tesouro SELIC 2029"],
                "acoes_br": ["ELET3", "SUZB3", "PRIO3"],
                "fii": ["HGBS11", "KNSC11"],
                "crypto": ["Bitcoin (BTC)"]
            },
            "rebalanceamento_necessario": moderado.get('sugestoes_transferencia', [])
        }

    except Exception as e:
        print(f"Erro ao buscar carteira recomendada: {e}")
        return {
            "erro": str(e),
            "perfil": "Conservador",
            "alocacao": {"rf": 75, "acoes_br": 15, "fii": 10}
        }

@router.post("/executar-card/{card_id}")
async def executar_card(card_id: int):
    """Marca um action card como executado"""
    try:
        query = """
            UPDATE action_cards
            SET status = 'executada', updated_at = NOW()
            WHERE id = %s
        """
        execute_query(query, (card_id,))

        return {
            "success": True,
            "message": "Card marcado como executado"
        }
    except Exception as e:
        return {
            "success": False,
            "erro": str(e)
        }

@router.post("/descartar-card/{card_id}")
async def descartar_card(card_id: int):
    """Descarta um action card"""
    try:
        query = """
            UPDATE action_cards
            SET status = 'descartada', updated_at = NOW()
            WHERE id = %s
        """
        execute_query(query, (card_id,))

        return {
            "success": True,
            "message": "Card descartado"
        }
    except Exception as e:
        return {
            "success": False,
            "erro": str(e)
        }
