"""
InvestAI - Chat Contextual com IA
Endpoint para chat que entende o contexto da página atual
Integrado com Orchestrator para contexto rico
"""
from fastapi import APIRouter
import os
from groq import Groq
from agents.orchestrator import Orchestrator

router = APIRouter()

# Inicializa Groq
groq_api_key = os.getenv('GROQ_API_KEY')
groq_client = None
if groq_api_key:
    groq_client = Groq(api_key=groq_api_key)

# Inicializa Orchestrator
orchestrator = Orchestrator()

@router.post("/context")
async def chat_contextual(payload: dict):
    """
    Chat contextual integrado com Orchestrator
    Recebe:
    - mensagem: pergunta do usuário
    - pagina_atual: nome da página
    - contexto_pagina: descrição do que a página mostra
    - historico_sessao: últimas 10 mensagens
    """
    mensagem = payload.get('mensagem', '')
    pagina = payload.get('pagina_atual', 'Dashboard')
    contexto_desc = payload.get('contexto_pagina', '')
    historico = payload.get('historico_sessao', [])

    try:
        # Usa orchestrator para chat contextual rico
        contexto = {
            'descricao': f"Página: {pagina}\n{contexto_desc}"
        }

        resultado = orchestrator.chat(mensagem, contexto)

        return {"resposta": resultado.get('resposta', 'Erro ao processar mensagem')}

    except Exception as e:
        print(f"Erro no chat: {e}")
        return {
            "resposta": "Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente."
        }

@router.post("/message")
async def chat_message(payload: dict):
    """
    Endpoint simplificado para chat (compatível com chat-widget.js)
    """
    mensagem = payload.get('mensagem', '') or payload.get('message', '')

    if not mensagem:
        return {"resposta": "Mensagem vazia"}

    try:
        resultado = orchestrator.chat(mensagem)
        return {"resposta": resultado.get('resposta', 'Erro ao processar mensagem')}

    except Exception as e:
        print(f"Erro no chat: {e}")
        return {
            "resposta": "Desculpe, ocorreu um erro. Tente novamente."
        }

@router.post("/analisar-ativo")
async def analisar_ativo(payload: dict):
    """Análise detalhada de um ativo específico"""
    ticker = payload.get('ticker', '')

    if not ticker:
        return {"erro": "Ticker não fornecido"}

    try:
        resultado = orchestrator.analisar_ativo(ticker)
        return resultado

    except Exception as e:
        print(f"Erro ao analisar {ticker}: {e}")
        return {"erro": str(e)}
