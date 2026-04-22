"""
InvestAI - Cenários Router
Scenario simulation with ML projections
"""
from fastapi import APIRouter
from pydantic import BaseModel
from api.database import execute_query
from ml.cenarios import CenariosML
import json

router = APIRouter()

cenarios_ml = CenariosML()

class CenarioSimular(BaseModel):
    capital_inicial: float
    perfil: str = "Moderado"
    horizonte_meses: int = 12

class AporteMensalSimular(BaseModel):
    valor_inicial: float
    aporte_mensal: float
    taxa_anual: float
    meses: int

class SelicSimular(BaseModel):
    valor: float
    taxa_selic: float = 10.75
    meses: int = 12

@router.get("/")
async def get_cenarios():
    """Retorna os 4 cenários com projeções ML completas"""
    try:
        # Busca valor total do portfolio
        query = "SELECT SUM(valor_atual) as total FROM portfolio"
        result = execute_query(query, fetch_one=True)
        total = float(result['total'] or 0) if result else 395000

        # Busca crypto
        query_crypto = "SELECT SUM(valor_brl) as total FROM portfolio_binance WHERE valor_brl > 0.01"
        crypto_result = execute_query(query_crypto, fetch_one=True)
        crypto_total = float(crypto_result['total'] or 0) if crypto_result else 0

        valor_total = total + crypto_total

        # Gera cenários com ML
        portfolio_data = {"total": valor_total}
        cenarios = cenarios_ml.gerar_cenarios(portfolio_data)

        return cenarios

    except Exception as e:
        print(f"Erro ao gerar cenários: {e}")
        # Fallback com cenários básicos
        return [
            {
                "id": 1,
                "nome": "Atual",
                "descricao": "88% Renda Fixa + 12% RV/FII",
                "alocacao": {"rf": 88, "acoes_br": 4, "fii": 8, "crypto": 0},
                "retorno_esperado_anual": 11.0,
                "risco": "Baixo"
            },
            {
                "id": 2,
                "nome": "Conservador",
                "descricao": "75% Renda Fixa + 25% RV/FII",
                "alocacao": {"rf": 75, "acoes_br": 10, "fii": 15, "crypto": 0},
                "retorno_esperado_anual": 11.5,
                "risco": "Baixo"
            },
            {
                "id": 3,
                "nome": "Moderado",
                "descricao": "60% RF + 35% RV/FII + 5% Crypto",
                "alocacao": {"rf": 60, "acoes_br": 15, "fii": 20, "crypto": 5},
                "retorno_esperado_anual": 13.0,
                "risco": "Médio"
            },
            {
                "id": 4,
                "nome": "Arrojado",
                "descricao": "40% RF + 50% RV/FII + 10% Crypto",
                "alocacao": {"rf": 40, "acoes_br": 30, "fii": 20, "crypto": 10},
                "retorno_esperado_anual": 16.0,
                "risco": "Alto"
            }
        ]

@router.post("/simular")
async def simular(req: CenarioSimular):
    """Simula cenário específico com capital e perfil customizados"""
    try:
        portfolio_data = {"total": req.capital_inicial}
        cenarios = cenarios_ml.gerar_cenarios(portfolio_data)

        # Filtra por perfil se especificado
        if req.perfil:
            cenario = next((c for c in cenarios if c['nome'].lower() == req.perfil.lower()), None)
            if cenario:
                return cenario

        return cenarios

    except Exception as e:
        print(f"Erro ao simular cenário: {e}")
        return {"erro": str(e)}

@router.post("/calcular-aporte-mensal")
async def calcular_aporte_mensal(req: AporteMensalSimular):
    """Calcula crescimento com aportes mensais"""
    try:
        resultado = cenarios_ml.simular_aporte_mensal(
            valor_inicial=req.valor_inicial,
            aporte_mensal=req.aporte_mensal,
            taxa_anual=req.taxa_anual / 100 if req.taxa_anual > 1 else req.taxa_anual,
            meses=req.meses
        )
        return resultado

    except Exception as e:
        print(f"Erro ao calcular aporte mensal: {e}")
        return {"erro": str(e)}

@router.post("/calcular-selic")
async def calcular_selic(req: SelicSimular):
    """Calcula retorno no Tesouro SELIC"""
    try:
        taxa_selic = req.taxa_selic / 100 if req.taxa_selic > 1 else req.taxa_selic

        resultado = cenarios_ml.calcular_selic_simulator(
            valor=req.valor,
            taxa_selic=taxa_selic,
            meses=req.meses
        )
        return resultado

    except Exception as e:
        print(f"Erro ao calcular SELIC: {e}")
        return {"erro": str(e)}

@router.get("/comparar")
async def comparar_cenarios():
    """Compara os 4 cenários lado a lado"""
    try:
        cenarios = await get_cenarios()

        # Monta comparação estruturada
        comparacao = {
            "metricas": [
                "Retorno Esperado (% a.a.)",
                "Volatilidade (% a.a.)",
                "Sharpe Ratio",
                "Renda Mensal (R$)",
                "Projeção 1 ano (R$)",
                "Projeção 3 anos (R$)",
                "Projeção 5 anos (R$)",
                "Max Drawdown (%)",
                "Risco"
            ],
            "cenarios": {}
        }

        for cenario in cenarios:
            nome = cenario['nome']
            comparacao['cenarios'][nome] = [
                cenario.get('retorno_esperado_anual', 0),
                cenario.get('volatilidade_anual', 0),
                cenario.get('sharpe_ratio', 0),
                cenario.get('renda_mensal', 0),
                cenario.get('projecoes', {}).get('1_ano', {}).get('valor', 0),
                cenario.get('projecoes', {}).get('3_anos', {}).get('valor', 0),
                cenario.get('projecoes', {}).get('5_anos', {}).get('valor', 0),
                cenario.get('max_drawdown', 0),
                cenario.get('risco', 'Médio')
            ]

        return comparacao

    except Exception as e:
        print(f"Erro ao comparar cenários: {e}")
        return {"erro": str(e)}

@router.get("/rebalanceamento/{cenario_nome}")
async def get_rebalanceamento(cenario_nome: str):
    """Retorna sugestões de rebalanceamento para um cenário"""
    try:
        cenarios = await get_cenarios()

        cenario = next((c for c in cenarios if c['nome'].lower() == cenario_nome.lower()), None)

        if not cenario:
            return {"erro": "Cenário não encontrado"}

        return {
            "cenario": cenario['nome'],
            "alocacao_atual": {
                "rf": 88,
                "acoes_br": 4,
                "fii": 8,
                "crypto": 0
            },
            "alocacao_nova": cenario['alocacao'],
            "sugestoes": cenario.get('sugestoes_transferencia', []),
            "beneficios": {
                "retorno_adicional": cenario.get('retorno_esperado_anual', 0) - 11.0,
                "renda_mensal_adicional": cenario.get('renda_mensal', 0) - 3500
            }
        }

    except Exception as e:
        print(f"Erro ao buscar rebalanceamento: {e}")
        return {"erro": str(e)}

@router.get("/detalhes/{cenario_nome}")
async def get_cenario_detalhes(cenario_nome: str):
    """Retorna detalhes completos de um cenário"""
    try:
        cenarios = await get_cenarios()

        cenario = next((c for c in cenarios if c['nome'].lower() == cenario_nome.lower()), None)

        if not cenario:
            return {"erro": "Cenário não encontrado"}

        return cenario

    except Exception as e:
        print(f"Erro ao buscar detalhes do cenário: {e}")
        return {"erro": str(e)}
