"""
InvestAI - API Principal
Plataforma 360° de inteligência financeira com agentes proativos
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()  # Loads .env from current working directory

from api.routers import auth, portfolio, exchanges, historico, cenarios, sugestoes, radar, smartmoney, chat_proativo, chat, plano
from feeds import moedas, binance, acoes_b3
from agents.orchestrator import Orchestrator

# Initialize orchestrator
orchestrator = Orchestrator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 InvestAI iniciando...")
    moedas.start_scheduler()
    binance.start_scheduler()
    acoes_b3.start_scheduler()
    orchestrator.start_scheduler()
    print("✅ InvestAI online na porta 8091")
    yield
    print("🛑 InvestAI encerrando...")
    orchestrator.stop_scheduler()

app = FastAPI(
    title="InvestAI",
    description="Plataforma 360° de Inteligência Financeira",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(exchanges.router, prefix="/api/exchanges", tags=["Exchanges"])
app.include_router(historico.router, prefix="/api/historico", tags=["Histórico"])
app.include_router(cenarios.router, prefix="/api/cenarios", tags=["Cenários"])
app.include_router(sugestoes.router, prefix="/api/sugestoes", tags=["Sugestões"])
app.include_router(radar.router, prefix="/api/radar", tags=["Radar"])
app.include_router(smartmoney.router, prefix="/api/smartmoney", tags=["Smart Money"])
app.include_router(chat_proativo.router, prefix="/api/chat/proativo", tags=["Chat Proativo"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(plano.router, prefix="/api/plano", tags=["Plano"])

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")

@app.get("/health")
async def health():
    return {"status": "ok", "database": "connected", "redis": "connected", "scheduler": "running"}

@app.get("/")
async def index():
    return FileResponse("dashboard/index.html")

@app.get("/{page}.html")
async def pages(page: str):
    return FileResponse(f"dashboard/{page}.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8091, reload=False)
