"""
InvestAI - Plano de Investimento Router
Step-by-step investment plan with SELIC calculator
"""
from fastapi import APIRouter
from pydantic import BaseModel
from api.database import execute_query
from ml.cenarios import CenariosML
from typing import List, Optional, Dict, Any
import json

router = APIRouter()

cenarios_ml = CenariosML()

class PlanoCreate(BaseModel):
    perfil: str  # 'conservador', 'moderado', 'arrojado'
    objetivos: List[str]
    horizonte_meses: int
    capital_inicial: float
    aporte_mensal: float = 0

class ChecklistUpdate(BaseModel):
    item_id: int
    concluido: bool

@router.get("/perfis")
async def get_perfis():
    """Retorna os 3 perfis de investidor"""
    return [
        {
            "id": "conservador",
            "nome": "Conservador",
            "descricao": "Prioriza segurança e preservação de capital",
            "alocacao_sugerida": {
                "rf": 75,
                "acoes_br": 10,
                "fii": 15,
                "crypto": 0
            },
            "retorno_esperado": "10-12% a.a.",
            "risco": "Baixo",
            "adequado_para": [
                "Reserva de emergência",
                "Objetivos de curto prazo (1-3 anos)",
                "Baixa tolerância a oscilações"
            ]
        },
        {
            "id": "moderado",
            "nome": "Moderado",
            "descricao": "Busca equilíbrio entre segurança e crescimento",
            "alocacao_sugerida": {
                "rf": 60,
                "acoes_br": 15,
                "fii": 20,
                "crypto": 5
            },
            "retorno_esperado": "12-15% a.a.",
            "risco": "Médio",
            "adequado_para": [
                "Objetivos de médio prazo (3-5 anos)",
                "Aposentadoria (10+ anos)",
                "Aceita oscilações moderadas"
            ]
        },
        {
            "id": "arrojado",
            "nome": "Arrojado",
            "descricao": "Foca em crescimento acelerado",
            "alocacao_sugerida": {
                "rf": 40,
                "acoes_br": 30,
                "fii": 20,
                "crypto": 10
            },
            "retorno_esperado": "15-20% a.a.",
            "risco": "Alto",
            "adequado_para": [
                "Objetivos de longo prazo (5+ anos)",
                "Alta tolerância a oscilações",
                "Busca por maior rentabilidade"
            ]
        }
    ]

@router.post("/criar")
async def criar_plano(plano: PlanoCreate):
    """Cria plano de investimento personalizado"""
    try:
        user_id = "hudson"  # TODO: pegar do auth

        # Insere plano
        query = """
            INSERT INTO plano_perfil
            (user_id, perfil, objetivos, horizonte_meses, capital_inicial, aporte_mensal)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = execute_query(
            query,
            (user_id, plano.perfil, json.dumps(plano.objetivos), plano.horizonte_meses,
             plano.capital_inicial, plano.aporte_mensal),
            fetch_one=True
        )

        plano_id = result['id']

        # Gera checklist baseado no perfil
        checklist_items = gerar_checklist(plano.perfil, plano_id, user_id)

        # Gera projeção
        portfolio_data = {"total": plano.capital_inicial}
        cenarios = cenarios_ml.gerar_cenarios(portfolio_data)
        cenario = next((c for c in cenarios if c['nome'].lower() == plano.perfil.lower()), cenarios[0])

        return {
            "success": True,
            "plano_id": plano_id,
            "perfil": plano.perfil,
            "cenario": cenario,
            "checklist": checklist_items,
            "projecao_final": calcular_projecao(plano, cenario)
        }

    except Exception as e:
        print(f"Erro ao criar plano: {e}")
        return {"success": False, "erro": str(e)}

def gerar_checklist(perfil: str, plano_id: int, user_id: str) -> List[Dict]:
    """Gera checklist de ações baseado no perfil"""
    checklists = {
        "conservador": [
            ("Abrir conta em corretora (BTG, XP, Rico)", "perfil"),
            ("Criar reserva de emergência (6 meses)", "objetivos"),
            ("Investir em Tesouro SELIC", "execucao"),
            ("Alocar em CDB 100%+ CDI", "execucao"),
            ("Diversificar com LCI/LCA", "execucao"),
            ("Configurar aportes automáticos", "execucao"),
            ("Revisar portfolio mensalmente", "alocacao")
        ],
        "moderado": [
            ("Abrir conta em corretora (BTG, XP, Rico)", "perfil"),
            ("Criar reserva de emergência (6 meses)", "objetivos"),
            ("Investir 60% em Renda Fixa (SELIC, CDB)", "alocacao"),
            ("Alocar 20% em FIIs (HGBS11, KNSC11)", "alocacao"),
            ("Investir 15% em Ações (ELET3, SUZB3, PRIO3)", "alocacao"),
            ("Considerar 5% em Crypto (BTC)", "alocacao"),
            ("Configurar aportes automáticos", "execucao"),
            ("Rebalancear trimestralmente", "execucao")
        ],
        "arrojado": [
            ("Abrir conta em corretora (BTG, XP, Rico)", "perfil"),
            ("Criar reserva de emergência (6 meses)", "objetivos"),
            ("Investir 40% em Renda Fixa", "alocacao"),
            ("Alocar 30% em Ações (diversificar 5+ tickers)", "alocacao"),
            ("Investir 20% em FIIs", "alocacao"),
            ("Alocar 10% em Crypto (BTC, ETH)", "alocacao"),
            ("Estudar análise fundamentalista", "perfil"),
            ("Acompanhar balanços trimestrais", "execucao"),
            ("Rebalancear semestralmente", "execucao")
        ]
    }

    items = checklists.get(perfil.lower(), checklists["moderado"])

    checklist = []
    for item_text, categoria in items:
        query = """
            INSERT INTO plano_checklist (user_id, plano_id, item, categoria)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        result = execute_query(query, (user_id, plano_id, item_text, categoria), fetch_one=True)

        checklist.append({
            "id": result['id'],
            "item": item_text,
            "categoria": categoria,
            "concluido": False
        })

    return checklist

def calcular_projecao(plano: PlanoCreate, cenario: Dict) -> Dict:
    """Calcula projeção de crescimento com aportes"""
    if plano.aporte_mensal > 0:
        resultado = cenarios_ml.simular_aporte_mensal(
            valor_inicial=plano.capital_inicial,
            aporte_mensal=plano.aporte_mensal,
            taxa_anual=cenario.get('retorno_esperado_anual', 12) / 100,
            meses=plano.horizonte_meses
        )
        return resultado
    else:
        # Sem aportes, apenas juros compostos
        taxa = cenario.get('retorno_esperado_anual', 12) / 100
        anos = plano.horizonte_meses / 12
        valor_final = plano.capital_inicial * ((1 + taxa) ** anos)

        return {
            'valor_final': round(valor_final, 2),
            'total_aportado': plano.capital_inicial,
            'ganho_total': round(valor_final - plano.capital_inicial, 2),
            'rentabilidade_percentual': round((valor_final - plano.capital_inicial) / plano.capital_inicial * 100, 2)
        }

@router.get("/meu-plano")
async def get_meu_plano():
    """Retorna plano ativo do usuário"""
    try:
        user_id = "hudson"  # TODO: pegar do auth

        query = """
            SELECT * FROM plano_perfil
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """
        plano = execute_query(query, (user_id,), fetch_one=True)

        if not plano:
            return {"existe": False}

        # Busca checklist
        query_checklist = """
            SELECT * FROM plano_checklist
            WHERE plano_id = %s
            ORDER BY categoria, id
        """
        checklist = execute_query(query_checklist, (plano['id'],))

        # Parse JSON
        plano['objetivos'] = json.loads(plano['objetivos']) if isinstance(plano['objetivos'], str) else plano['objetivos']

        return {
            "existe": True,
            "plano": dict(plano),
            "checklist": [dict(item) for item in checklist] if checklist else []
        }

    except Exception as e:
        print(f"Erro ao buscar plano: {e}")
        return {"existe": False, "erro": str(e)}

@router.post("/checklist/atualizar")
async def atualizar_checklist(update: ChecklistUpdate):
    """Atualiza status de um item do checklist"""
    try:
        query = """
            UPDATE plano_checklist
            SET concluido = %s,
                data_conclusao = CASE WHEN %s THEN NOW() ELSE NULL END
            WHERE id = %s
        """
        execute_query(query, (update.concluido, update.concluido, update.item_id))

        return {"success": True}

    except Exception as e:
        print(f"Erro ao atualizar checklist: {e}")
        return {"success": False, "erro": str(e)}

@router.post("/calcular-selic")
async def calcular_selic(payload: dict):
    """Calcula retorno do Tesouro SELIC"""
    valor = float(payload.get('valor', 1000))
    taxa_selic = float(payload.get('taxa_selic', 10.75))
    meses = int(payload.get('meses', 12))

    try:
        resultado = cenarios_ml.calcular_selic_simulator(
            valor=valor,
            taxa_selic=taxa_selic / 100 if taxa_selic > 1 else taxa_selic,
            meses=meses
        )
        return resultado

    except Exception as e:
        print(f"Erro ao calcular SELIC: {e}")
        return {"erro": str(e)}

@router.get("/guias/{perfil}")
async def get_guia_perfil(perfil: str):
    """Retorna guia detalhado por perfil"""
    guias = {
        "conservador": {
            "titulo": "Guia do Investidor Conservador",
            "resumo": "Foco em segurança e preservação de capital",
            "passos": [
                {
                    "numero": 1,
                    "titulo": "Crie sua reserva de emergência",
                    "descricao": "6 meses de despesas em investimentos líquidos (Tesouro SELIC, CDB com liquidez diária)",
                    "onde_investir": ["Tesouro SELIC", "CDB Liquidez Diária 100% CDI", "Nubank (100% CDI)"]
                },
                {
                    "numero": 2,
                    "titulo": "Diversifique em Renda Fixa",
                    "descricao": "Aloque 75% do portfolio em produtos de RF com boa rentabilidade",
                    "onde_investir": ["CDB BTG 103% CDI", "LCI Banco Inter 94% CDI", "Tesouro SELIC 2029"]
                },
                {
                    "numero": 3,
                    "titulo": "Adicione FIIs para renda passiva",
                    "descricao": "15% em FIIs de papel para receber dividendos mensais isentos de IR",
                    "onde_investir": ["HGBS11 (DY 9.96%)", "KNSC11 (DY 12.64%)", "MXRF11"]
                },
                {
                    "numero": 4,
                    "titulo": "Pequena exposição em ações",
                    "descricao": "10% em ações de empresas sólidas para crescimento de longo prazo",
                    "onde_investir": ["ELET3 (Eletrobras)", "ITUB4 (Itaú)", "VALE3 (Vale)"]
                }
            ]
        },
        "moderado": {
            "titulo": "Guia do Investidor Moderado",
            "resumo": "Equilíbrio entre segurança e crescimento",
            "passos": [
                {
                    "numero": 1,
                    "titulo": "Mantenha 60% em Renda Fixa",
                    "descricao": "Base sólida para estabilidade e proteção",
                    "onde_investir": ["CDB 103% CDI", "Tesouro IPCA+ 2035", "LCI/LCA"]
                },
                {
                    "numero": 2,
                    "titulo": "20% em Fundos Imobiliários",
                    "descricao": "Diversifique em FIIs de papel e tijolo",
                    "onde_investir": ["HGBS11", "KNSC11", "MXRF11", "HGLG11"]
                },
                {
                    "numero": 3,
                    "titulo": "15% em Ações",
                    "descricao": "Portfolio diversificado de 5-8 ações",
                    "onde_investir": ["ELET3", "SUZB3", "PRIO3", "VALE3", "ITUB4"]
                },
                {
                    "numero": 4,
                    "titulo": "5% em Criptomoedas",
                    "descricao": "Exposição controlada para potencial de crescimento",
                    "onde_investir": ["Bitcoin (BTC)", "Ethereum (ETH)"]
                }
            ]
        },
        "arrojado": {
            "titulo": "Guia do Investidor Arrojado",
            "resumo": "Crescimento acelerado com risco controlado",
            "passos": [
                {
                    "numero": 1,
                    "titulo": "40% em Renda Fixa",
                    "descricao": "Base de segurança menor mas ainda importante",
                    "onde_investir": ["CDB 103% CDI", "Tesouro IPCA+", "Debêntures incentivadas"]
                },
                {
                    "numero": 2,
                    "titulo": "30% em Ações",
                    "descricao": "Portfolio agressivo com 10+ ações",
                    "onde_investir": ["Small Caps", "ELET3", "PRIO3", "SUZB3", "Ações growth"]
                },
                {
                    "numero": 3,
                    "titulo": "20% em FIIs",
                    "descricao": "Mix de FIIs de papel e tijolo para renda",
                    "onde_investir": ["HGBS11", "KNSC11", "Shopping centers", "Logística"]
                },
                {
                    "numero": 4,
                    "titulo": "10% em Crypto",
                    "descricao": "Exposição significativa para alto crescimento",
                    "onde_investir": ["Bitcoin (BTC)", "Ethereum (ETH)", "Altcoins selecionadas"]
                }
            ]
        }
    }

    guia = guias.get(perfil.lower())

    if not guia:
        return {"erro": "Perfil não encontrado"}

    return guia
