from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os

SECRET = os.getenv("JWT_SECRET", "investai_jwt_secret_2026_hudson")

# Autenticação via JWT
reusable_oauth2 = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=["HS256"])
        return {"username": payload["sub"]}
    except (jwt.PyJWTError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication credentials",
        )