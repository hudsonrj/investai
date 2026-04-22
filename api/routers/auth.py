from fastapi import APIRouter, Response, Cookie, HTTPException
from pydantic import BaseModel
import jwt
import os
from datetime import datetime, timedelta

router = APIRouter()
SECRET = os.getenv("JWT_SECRET", "investai_jwt_secret_2026_hudson")

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(req: LoginRequest, response: Response):
    if req.username == "hudson" and req.password == "hudson2026":
        token = jwt.encode({"sub": req.username, "exp": datetime.utcnow() + timedelta(days=7)}, SECRET, algorithm="HS256")
        response.set_cookie("investai_token", token, httponly=True, samesite="lax", max_age=604800)
        return {"status": "success", "user": req.username}
    return {"status": "error", "message": "Credenciais inválidas"}

@router.get("/me")
async def me(investai_token: str = Cookie(None)):
    if not investai_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(investai_token, SECRET, algorithms=["HS256"])
        return {"username": payload["sub"]}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/check")
async def check(investai_token: str = Cookie(None)):
    """Verifica se está autenticado (endpoint simples)"""
    if not investai_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        jwt.decode(investai_token, SECRET, algorithms=["HS256"])
        return {"authenticated": True}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("investai_token")
    return {"status": "logged out"}
