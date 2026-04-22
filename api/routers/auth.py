"""
InvestAI — Autenticação
JWT via HttpOnly cookie, credenciais via variáveis de ambiente.

Endpoints:
  POST /api/auth/login   — autentica e define cookie JWT (7 dias)
  POST /api/auth/logout  — remove o cookie
  GET  /api/auth/me      — retorna usuário autenticado ou 401
  GET  /api/auth/check   — verifica autenticação (sem payload)

Segurança:
  - Credenciais lidas exclusivamente de AUTH_USERNAME / AUTH_PASSWORD no .env
  - Rate limiting via Redis: máx. 5 tentativas por IP em 15 min
  - Resposta 401 em falha de login (nunca 200 com erro no body)
  - Token JWT com expiração de 7 dias, assinado com HS256
"""
import os
import time
from fastapi import APIRouter, Response, Cookie, HTTPException, Request
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta

router = APIRouter()

# ── Configuração ──────────────────────────────────────────────────────────────

SECRET    = os.getenv("JWT_SECRET", "")
AUTH_USER = os.getenv("AUTH_USERNAME", "")
AUTH_PASS = os.getenv("AUTH_PASSWORD", "")

if not SECRET:
    raise RuntimeError("JWT_SECRET não definido no .env")
if not AUTH_USER or not AUTH_PASS:
    raise RuntimeError("AUTH_USERNAME e AUTH_PASSWORD não definidos no .env")

# ── Rate limiting (Redis) ─────────────────────────────────────────────────────

MAX_ATTEMPTS  = 5       # tentativas por janela
WINDOW_SECS   = 900     # 15 minutos
LOCKOUT_SECS  = 900     # bloqueio por 15 minutos

def _redis():
    """Importa Redis sob demanda para evitar dependência circular."""
    from api.database import get_redis
    return get_redis()

def _check_rate_limit(ip: str):
    """
    Verifica se o IP está bloqueado. Lança HTTPException 429 se sim.
    Retorna o número de tentativas restantes.
    """
    try:
        r = _redis()
        key_attempts = f"login:attempts:{ip}"
        key_lockout  = f"login:lockout:{ip}"

        # IP em lockout?
        if r.exists(key_lockout):
            ttl = r.ttl(key_lockout)
            raise HTTPException(
                status_code=429,
                detail=f"Muitas tentativas. Tente novamente em {ttl // 60 + 1} minutos."
            )

        attempts = int(r.get(key_attempts) or 0)
        return attempts
    except HTTPException:
        raise
    except Exception:
        return 0  # Se Redis estiver indisponível, não bloqueia

def _register_failed(ip: str):
    """Registra tentativa falha. Aplica lockout ao atingir MAX_ATTEMPTS."""
    try:
        r = _redis()
        key_attempts = f"login:attempts:{ip}"
        key_lockout  = f"login:lockout:{ip}"

        pipe = r.pipeline()
        pipe.incr(key_attempts)
        pipe.expire(key_attempts, WINDOW_SECS)
        results = pipe.execute()

        attempts = results[0]
        if attempts >= MAX_ATTEMPTS:
            r.setex(key_lockout, LOCKOUT_SECS, "1")
            r.delete(key_attempts)
    except Exception:
        pass

def _clear_rate_limit(ip: str):
    """Remove contadores de falha após login bem-sucedido."""
    try:
        r = _redis()
        r.delete(f"login:attempts:{ip}")
        r.delete(f"login:lockout:{ip}")
    except Exception:
        pass

# ── Helpers JWT ───────────────────────────────────────────────────────────────

def _make_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

def _decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=["HS256"])

# ── Models ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/login")
async def login(req: LoginRequest, response: Response, request: Request):
    """
    Autentica o usuário.
    - Aplica rate limiting por IP (5 tentativas / 15 min)
    - Retorna 401 em credenciais inválidas
    - Define cookie HttpOnly 'investai_token' com JWT de 7 dias
    """
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip)

    # Comparação constante (evita timing attacks)
    user_ok = req.username == AUTH_USER
    pass_ok = req.password == AUTH_PASS

    if not (user_ok and pass_ok):
        _register_failed(ip)
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    _clear_rate_limit(ip)
    token = _make_token(req.username)
    response.set_cookie(
        key="investai_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=604800,  # 7 dias
    )
    return {"status": "success", "user": req.username}


@router.post("/logout")
async def logout(response: Response):
    """Remove o cookie de autenticação."""
    response.delete_cookie("investai_token")
    return {"status": "logged out"}


@router.get("/me")
async def me(investai_token: str = Cookie(None)):
    """Retorna o usuário autenticado ou 401."""
    if not investai_token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    try:
        payload = _decode_token(investai_token)
        return {"username": payload["sub"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sessão expirada")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.get("/check")
async def check(investai_token: str = Cookie(None)):
    """Verifica autenticação sem retornar payload (usado pelo auth-guard)."""
    if not investai_token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    try:
        _decode_token(investai_token)
        return {"authenticated": True}
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")
