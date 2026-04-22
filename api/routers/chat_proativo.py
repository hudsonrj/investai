"""
Chat Proativo — InvestAI
Gera um insight proativo baseado em dados reais do mercado.
"""
from fastapi import APIRouter, Depends
from api.middleware.auth_middleware import get_current_user
from api.database import execute_query
import os, httpx, json
from datetime import datetime

router = APIRouter()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

# In-memory store for pending proactive insight
_pending_insight: dict = {}


@router.get("")
@router.get("/")
async def get_proativo():
    """Returns pending proactive insight (if any) for polling by chat-widget."""
    global _pending_insight
    if _pending_insight.get("ok") and _pending_insight.get("mensagem"):
        return _pending_insight
    return {"ok": False, "mensagem": None}


@router.post("/limpar")
async def limpar_proativo():
    """Clears the pending proactive insight."""
    global _pending_insight
    _pending_insight = {}
    return {"ok": True}


async def _fetch_market_context() -> dict:
    """Coleta contexto de mercado: watchlist + briefing + sugestões recentes."""
    ctx = {}

    # Watchlist
    try:
        wl = execute_query(
            "SELECT ticker, entrada, alvo, stop, observacoes FROM watchlist ORDER BY ticker",
            fetch_all=True
        )
        ctx["watchlist"] = wl or []
    except Exception:
        ctx["watchlist"] = []

    # Briefing mais recente
    try:
        briefing = execute_query(
            "SELECT titulo, conteudo, timestamp FROM briefings ORDER BY timestamp DESC LIMIT 1",
            fetch_one=True
        )
        ctx["briefing"] = briefing or {}
    except Exception:
        ctx["briefing"] = {}

    # Sugestões novas
    try:
        sugs = execute_query(
            "SELECT titulo, descricao, tipo FROM sugestoes WHERE status='nova' ORDER BY created_at DESC LIMIT 3",
            fetch_all=True
        )
        ctx["sugestoes"] = sugs or []
    except Exception:
        ctx["sugestoes"] = []

    # Hora do dia para calibrar urgência
    ctx["hora_utc"] = datetime.utcnow().strftime("%H:%M")
    ctx["dia_semana"] = datetime.utcnow().strftime("%A")

    return ctx


async def _gerar_insight_groq(ctx: dict) -> dict:
    """Chama Groq para gerar insight proativo. Retorna {ok, titulo, mensagem, urgencia}."""
    prompt = f"""Você é o InvestAI, assistente de investimentos proativo do Hudson.
Hora atual (UTC): {ctx.get('hora_utc')} | Dia: {ctx.get('dia_semana')}

Carteira em watchlist: {json.dumps(ctx.get('watchlist', []), ensure_ascii=False)}
Briefing recente: {json.dumps(ctx.get('briefing', {}), ensure_ascii=False)}
Sugestões ativas: {json.dumps(ctx.get('sugestoes', []), ensure_ascii=False)}

Gere UM insight proativo e relevante para o Hudson agora.
Responda APENAS JSON com este formato:
{{
  "ok": true,
  "titulo": "título curto (max 8 palavras)",
  "mensagem": "insight direto em 2-3 frases max, com dado concreto",
  "urgencia": "normal" ou "urgente"
}}

Se não houver nada relevante no momento, retorne: {{"ok": false, "motivo": "sem alertas"}}
"""
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 300
                }
            )
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            # Remove markdown code fences if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
    except Exception as e:
        # Fallback com insight genérico baseado na hora
        hora = int(ctx.get("hora_utc", "00:00").split(":")[0])
        if hora >= 20:
            return {
                "ok": True,
                "titulo": "Revisão noturna da carteira",
                "mensagem": "Boa noite! Antes de encerrar o dia, revise sua watchlist e verifique se alguma posição atingiu o alvo ou stop. Disciplina é a chave do investidor de sucesso.",
                "urgencia": "normal"
            }
        return {"ok": False, "motivo": f"erro groq: {e}"}


@router.post("/gerar")
async def gerar_proativo(current_user: dict = Depends(get_current_user)):
    """Gera insight proativo baseado no contexto atual do mercado."""
    ctx = await _fetch_market_context()
    resultado = await _gerar_insight_groq(ctx)
    return resultado
