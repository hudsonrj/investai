"""
InvestAI - Orchestrator (Multi-Agent Coordinator)
Coordinates all AI agents and schedules proactive briefings:
- Suggestion Engine (action cards)
- ML Scenarios
- Market analysis
- Cron jobs for briefings (09:00, 13:00, 21:00 UTC)
"""
import os
from datetime import datetime
from typing import Dict, Any
from groq import Groq
from apscheduler.schedulers.background import BackgroundScheduler
from agents.suggestion_engine import SuggestionEngine
from ml.cenarios import CenariosML
from api.database import execute_query, get_redis

class Orchestrator:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.client = Groq(api_key=self.groq_key) if self.groq_key else None
        self.redis = get_redis()
        self.scheduler = BackgroundScheduler()

        # Agents
        self.suggestion_engine = SuggestionEngine()
        self.cenarios_ml = CenariosML()

    def start_scheduler(self):
        """Inicia scheduler para briefings proativos"""
        # Briefings diários em 3 horários: 09:00, 13:00, 21:00 UTC
        self.scheduler.add_job(
            self.gerar_briefing_proativo,
            'cron',
            hour=9,
            minute=0,
            id='briefing_manha'
        )
        self.scheduler.add_job(
            self.gerar_briefing_proativo,
            'cron',
            hour=13,
            minute=0,
            id='briefing_tarde'
        )
        self.scheduler.add_job(
            self.gerar_briefing_proativo,
            'cron',
            hour=21,
            minute=0,
            id='briefing_noite'
        )

        # Atualiza action cards a cada 2 horas
        self.scheduler.add_job(
            self.atualizar_action_cards,
            'interval',
            hours=2,
            id='update_cards'
        )

        self.scheduler.start()
        print("🤖 Orchestrator iniciado - Briefings agendados (09:00, 13:00, 21:00 UTC)")

    def gerar_briefing_proativo(self):
        """Gera briefing proativo e notifica usuário"""
        try:
            print(f"[{datetime.now()}] Gerando briefing proativo...")

            briefing = self.suggestion_engine.gerar_briefing_diario()

            # Notifica via Redis (para WebSocket/Push notification)
            self.redis.publish('investai_briefings', briefing['conteudo'])

            print(f"✓ Briefing gerado: {briefing['titulo']}")

            return briefing

        except Exception as e:
            print(f"Erro ao gerar briefing: {e}")
            return None

    def atualizar_action_cards(self):
        """Atualiza action cards"""
        try:
            print(f"[{datetime.now()}] Atualizando action cards...")

            cards = self.suggestion_engine.gerar_action_cards()

            print(f"✓ {len(cards)} action cards gerados")

            return cards

        except Exception as e:
            print(f"Erro ao atualizar action cards: {e}")
            return []

    def chat(self, mensagem: str, contexto: Dict = None) -> Dict[str, Any]:
        """
        Chat contextual que integra todos os dados do sistema
        """
        if not self.client:
            return {
                "resposta": "IA não configurada. Verifique GROQ_API_KEY.",
                "modelo": "demo"
            }

        try:
            # Monta contexto rico
            system_context = self._montar_contexto_sistema()

            # Adiciona contexto da página se fornecido
            if contexto:
                page_context = f"\n\nCONTEXTO DA PÁGINA:\n{contexto.get('descricao', '')}"
                system_context += page_context

            # Verifica se é pergunta sobre portfolio
            if any(palavra in mensagem.lower() for palavra in ['portfolio', 'carteira', 'investimento', 'quanto']):
                portfolio_info = self._buscar_info_portfolio()
                system_context += f"\n\nDADOS DO PORTFOLIO:\n{portfolio_info}"

            # Verifica se é pergunta sobre watchlist
            if any(palavra in mensagem.lower() for palavra in ['watchlist', 'ação', 'ticker', 'vale']):
                watchlist_info = self._buscar_info_watchlist()
                system_context += f"\n\nWATCHLIST:\n{watchlist_info}"

            messages = [
                {"role": "system", "content": system_context},
                {"role": "user", "content": mensagem}
            ]

            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=600
            )

            resposta = completion.choices[0].message.content

            return {
                "resposta": resposta,
                "modelo": "groq/llama-3.3-70b",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Erro no chat: {e}")
            return {
                "resposta": f"Desculpe, ocorreu um erro: {str(e)}",
                "modelo": "erro"
            }

    def _montar_contexto_sistema(self) -> str:
        """Monta contexto rico do sistema para a IA"""
        return """Você é o InvestAI Assistant, um assistente de investimentos inteligente e proativo.

SUAS CAPACIDADES:
- Análise de portfolio e rebalanceamento
- Sugestões de ações, FIIs e criptomoedas
- Cálculos de rentabilidade e projeções
- Análise de risco e diversificação
- Educação financeira

DIRETRIZES:
- Seja direto, prático e útil
- Use dados reais quando disponível
- Explique conceitos de forma simples
- Sempre considere o perfil conservador/moderado do usuário
- Sugira ações concretas quando relevante
- Fale em português brasileiro
- Use emojis quando apropriado (mas sem exagero)

MERCADO ATUAL (Brasil):
- SELIC: 14.75% a.a.
- CDI: 14.65% a.a.
- IPCA: 4.83% a.a.
- USD/BRL: ~R$ 5.05

ESPECIALIDADES:
- Tesouro Direto, CDBs, LCIs
- Fundos Imobiliários (FIIs)
- Ações brasileiras (B3)
- Criptomoedas (Binance)
- Cenários de investimento"""

    def _buscar_info_portfolio(self) -> str:
        """Busca informações do portfolio para contexto"""
        try:
            query = """
                SELECT
                    SUM(valor_atual) as total,
                    SUM(CASE WHEN tipo='Renda Fixa' THEN valor_atual ELSE 0 END) as rf,
                    SUM(CASE WHEN tipo='Ações' THEN valor_atual ELSE 0 END) as rv,
                    SUM(CASE WHEN tipo='Previdência' THEN valor_atual ELSE 0 END) as prev
                FROM portfolio
            """
            result = execute_query(query, fetch_one=True)

            if result:
                total = float(result['total'] or 0)
                rf = float(result['rf'] or 0)
                rv = float(result['rv'] or 0)
                prev = float(result['prev'] or 0)

                # Busca crypto
                query_crypto = "SELECT SUM(valor_brl) as total FROM portfolio_binance WHERE valor_brl > 0.01"
                crypto_result = execute_query(query_crypto, fetch_one=True)
                crypto = float(crypto_result['total'] or 0) if crypto_result else 0

                total_geral = total + crypto

                return f"""Portfolio Total: R$ {total_geral:,.2f}
- Renda Fixa: R$ {rf:,.2f} ({rf/total_geral*100:.1f}%)
- Ações: R$ {rv:,.2f} ({rv/total_geral*100:.1f}%)
- Previdência: R$ {prev:,.2f} ({prev/total_geral*100:.1f}%)
- Crypto: R$ {crypto:,.2f} ({crypto/total_geral*100:.1f}%)"""

        except Exception as e:
            return f"Erro ao buscar portfolio: {e}"

    def _buscar_info_watchlist(self) -> str:
        """Busca informações da watchlist para contexto"""
        try:
            query = "SELECT ticker, nome, entrada, alvo, stop FROM watchlist ORDER BY ticker"
            watchlist = execute_query(query)

            if watchlist:
                linhas = []
                for item in watchlist:
                    ticker = item['ticker']
                    entrada = float(item['entrada'] or 0)
                    alvo = float(item['alvo'] or 0)
                    ganho_pot = ((alvo - entrada) / entrada * 100) if entrada > 0 else 0

                    linhas.append(f"- {ticker}: Entrada R$ {entrada:.2f} | Alvo R$ {alvo:.2f} (+{ganho_pot:.1f}%)")

                return "\n".join(linhas)
            else:
                return "Watchlist vazia"

        except Exception as e:
            return f"Erro ao buscar watchlist: {e}"

    def analisar_ativo(self, ticker: str) -> Dict[str, Any]:
        """Analisa um ativo específico com IA"""
        if not self.client:
            return {"erro": "IA não configurada"}

        try:
            # Busca dados do ativo (se na watchlist)
            query = "SELECT * FROM watchlist WHERE ticker = %s"
            ativo = execute_query(query, (ticker,), fetch_one=True)

            # Busca preço atual via yfinance
            import yfinance as yf

            ticker_sa = ticker + '.SA' if not ticker.endswith('.SA') else ticker
            stock = yf.Ticker(ticker_sa)
            info = stock.info
            hist = stock.history(period='1mo')

            preco_atual = hist['Close'].iloc[-1] if len(hist) > 0 else 0

            # Monta contexto para IA
            contexto = f"""Analise o ativo {ticker}:

DADOS ATUAIS:
- Preço atual: R$ {preco_atual:.2f}
- Nome: {info.get('longName', 'N/A')}
- Setor: {info.get('sector', 'N/A')}

"""

            if ativo:
                entrada = float(ativo['entrada'] or 0)
                alvo = float(ativo['alvo'] or 0)
                stop = float(ativo['stop'] or 0) if ativo['stop'] else None

                ganho_pot = ((alvo - preco_atual) / preco_atual * 100) if preco_atual > 0 else 0
                risco = ((preco_atual - stop) / preco_atual * 100) if stop and preco_atual > 0 else 0

                contexto += f"""WATCHLIST:
- Entrada: R$ {entrada:.2f}
- Alvo: R$ {alvo:.2f}
- Stop: R$ {stop:.2f if stop else 'N/A'}
- Ganho potencial: {ganho_pot:.1f}%
- Risco: {risco:.1f}%

Baseado nesses dados, responda:
1. Vale a pena investir agora?
2. Qual o risco?
3. Qual o potencial de ganho?

Seja direto e objetivo."""

            messages = [
                {"role": "system", "content": "Você é um analista de investimentos. Seja objetivo e prático."},
                {"role": "user", "content": contexto}
            ]

            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.5,
                max_tokens=400
            )

            analise = completion.choices[0].message.content

            return {
                "ticker": ticker,
                "preco_atual": round(preco_atual, 2),
                "analise": analise,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Erro ao analisar {ticker}: {e}")
            return {"erro": str(e)}

    def calcular_rebalanceamento(self, cenario: str) -> Dict[str, Any]:
        """Calcula rebalanceamento para um cenário específico"""
        try:
            # Busca portfolio atual
            query = "SELECT SUM(valor_atual) as total FROM portfolio"
            result = execute_query(query, fetch_one=True)
            total = float(result['total'] or 0) if result else 395000

            # Busca crypto
            query_crypto = "SELECT SUM(valor_brl) as total FROM portfolio_binance"
            crypto_result = execute_query(query_crypto, fetch_one=True)
            crypto_total = float(crypto_result['total'] or 0) if crypto_result else 0

            valor_total = total + crypto_total

            # Gera cenários
            portfolio_data = {"total": valor_total}
            cenarios = self.cenarios_ml.gerar_cenarios(portfolio_data)

            # Encontra cenário solicitado
            cenario_selecionado = next((c for c in cenarios if c['nome'].lower() == cenario.lower()), None)

            if cenario_selecionado:
                return cenario_selecionado
            else:
                return {"erro": f"Cenário '{cenario}' não encontrado"}

        except Exception as e:
            print(f"Erro ao calcular rebalanceamento: {e}")
            return {"erro": str(e)}

    def stop_scheduler(self):
        """Para o scheduler"""
        self.scheduler.shutdown()
        print("🛑 Orchestrator parado")
