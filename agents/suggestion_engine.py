"""
InvestAI - Suggestion Engine (Mentor Ativo)
Generates proactive action cards and briefings based on:
- Portfolio analysis
- Market opportunities
- Watchlist alerts
- News sentiment
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import yfinance as yf
import requests
from groq import Groq
from api.database import execute_query, get_redis

class SuggestionEngine:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.client = Groq(api_key=self.groq_key) if self.groq_key else None
        self.redis = get_redis()

    def gerar_action_cards(self) -> List[Dict[str, Any]]:
        """Gera cartões de ação baseados em análise multi-dimensional"""
        cards = []

        # 1. Analisa portfolio atual
        portfolio_cards = self._analise_portfolio()
        cards.extend(portfolio_cards)

        # 2. Analisa watchlist
        watchlist_cards = self._analise_watchlist()
        cards.extend(watchlist_cards)

        # 3. Detecta oportunidades de mercado
        mercado_cards = self._analise_mercado()
        cards.extend(mercado_cards)

        # 4. Analisa notícias com IA
        news_cards = self._analise_noticias()
        cards.extend(news_cards)

        # Salva no banco
        self._salvar_cards(cards)

        # Retorna top 6 cards por prioridade
        cards_sorted = sorted(cards, key=lambda x: (x.get('prioridade', 3), x.get('ganho_potencial', 0)), reverse=True)
        return cards_sorted[:6]

    def _analise_portfolio(self) -> List[Dict]:
        """Analisa portfolio atual e sugere rebalanceamentos"""
        cards = []

        try:
            # Busca resumo do portfolio
            query = """
                SELECT
                    SUM(CASE WHEN tipo='Renda Fixa' THEN valor_atual ELSE 0 END) as rf,
                    SUM(CASE WHEN tipo='Ações' THEN valor_atual ELSE 0 END) as rv,
                    SUM(CASE WHEN tipo='Previdência' THEN valor_atual ELSE 0 END) as prev,
                    SUM(valor_atual) as total
                FROM portfolio
            """
            result = execute_query(query, fetch_one=True)

            if result:
                total = float(result['total'] or 0)
                rf_pct = (float(result['rf'] or 0) / total * 100) if total > 0 else 0
                rv_pct = (float(result['rv'] or 0) / total * 100) if total > 0 else 0

                # Busca total Binance (crypto)
                query_binance = "SELECT SUM(valor_brl) as total FROM portfolio_binance WHERE valor_brl > 0.01"
                binance_result = execute_query(query_binance, fetch_one=True)
                crypto_total = float(binance_result['total'] or 0) if binance_result else 0

                total_geral = total + crypto_total
                crypto_pct = (crypto_total / total_geral * 100) if total_geral > 0 else 0

                # CARD 1: Se alta concentração em RF (>80%)
                if rf_pct > 80:
                    cards.append({
                        'tipo': 'rebalanceamento',
                        'titulo': 'Portfolio muito conservador',
                        'descricao': f'Você tem {rf_pct:.1f}% em Renda Fixa. Considere diversificar para aumentar rentabilidade.',
                        'justificativa': f'Com SELIC a 10.75%, RF rende ~11% a.a. Diversificar 15-20% em RV pode trazer retorno de 15-20% a.a.',
                        'acoes_sugeridas': [
                            {'label': 'Ver cenários', 'acao': 'cenarios'},
                            {'label': 'Simular rebalanceamento', 'acao': 'simular'}
                        ],
                        'prioridade': 1,
                        'risco': 'medio'
                    })

                # CARD 2: Se sem exposição crypto (<1%)
                if crypto_pct < 1:
                    cards.append({
                        'tipo': 'oportunidade',
                        'titulo': 'Sem exposição a criptomoedas',
                        'ticker': 'BTC',
                        'descricao': 'Considere alocar 2-5% em Bitcoin como proteção contra inflação.',
                        'justificativa': 'BTC historicamente se valorizou 100-200% a.a. em média nos últimos 10 anos.',
                        'ganho_potencial': 50.0,
                        'acoes_sugeridas': [
                            {'label': 'Ver análise BTC', 'acao': 'ver_ativo', 'ticker': 'BTC'},
                            {'label': 'Como comprar', 'acao': 'educacional'}
                        ],
                        'prioridade': 2,
                        'risco': 'alto'
                    })

                # CARD 3: Se sem FIIs
                query_fii = "SELECT COUNT(*) as cnt FROM portfolio WHERE tipo LIKE '%FII%'"
                fii_result = execute_query(query_fii, fetch_one=True)
                if fii_result and fii_result['cnt'] == 0:
                    cards.append({
                        'tipo': 'oportunidade',
                        'titulo': 'Considere Fundos Imobiliários',
                        'ticker': 'HGBS11',
                        'descricao': 'FIIs pagam rendimentos mensais isentos de IR. HGBS11 tem DY de 9.96%.',
                        'justificativa': 'Diversificação + renda passiva mensal + isenção fiscal.',
                        'ganho_potencial': 9.96,
                        'acoes_sugeridas': [
                            {'label': 'Adicionar à watchlist', 'acao': 'add_watchlist', 'ticker': 'HGBS11'},
                            {'label': 'Ver detalhes', 'acao': 'ver_ativo', 'ticker': 'HGBS11'}
                        ],
                        'prioridade': 2,
                        'risco': 'medio'
                    })

        except Exception as e:
            print(f"Erro na análise de portfolio: {e}")

        return cards

    def _analise_watchlist(self) -> List[Dict]:
        """Analisa watchlist e gera alertas"""
        cards = []

        try:
            query = "SELECT * FROM watchlist ORDER BY ticker"
            watchlist = execute_query(query)

            for item in watchlist:
                ticker = item['ticker']
                entrada = float(item['entrada'] or 0)
                alvo = float(item['alvo'] or 0)
                stop = float(item['stop'] or 0) if item['stop'] else None

                # Busca preço atual
                try:
                    ticker_sa = ticker + '.SA' if not ticker.endswith('.SA') else ticker
                    stock = yf.Ticker(ticker_sa)
                    hist = stock.history(period='1d')

                    if len(hist) > 0:
                        preco_atual = hist['Close'].iloc[-1]

                        # Calcula métricas
                        ganho_potencial = ((alvo - preco_atual) / preco_atual * 100) if preco_atual > 0 else 0
                        risco = ((preco_atual - stop) / preco_atual * 100) if stop and preco_atual > 0 else 10
                        assimetria = abs(ganho_potencial / risco) if risco > 0 else 0

                        # ALERTA: Preço próximo do alvo (>80%)
                        progresso = ((preco_atual - entrada) / (alvo - entrada) * 100) if (alvo - entrada) > 0 else 0

                        if progresso >= 80:
                            cards.append({
                                'tipo': 'alerta',
                                'titulo': f'{ticker} próximo do alvo!',
                                'ticker': ticker,
                                'preco_atual': round(preco_atual, 2),
                                'preco_alvo': alvo,
                                'descricao': f'{ticker} está a {100-progresso:.1f}% do alvo. Considere realizar lucro.',
                                'justificativa': f'Preço atual: R$ {preco_atual:.2f} | Alvo: R$ {alvo:.2f}',
                                'ganho_potencial': round(ganho_potencial, 2),
                                'acoes_sugeridas': [
                                    {'label': 'Ver gráfico', 'acao': 'ver_grafico', 'ticker': ticker},
                                    {'label': 'Realizar lucro', 'acao': 'executar'}
                                ],
                                'prioridade': 1,
                                'risco': 'baixo'
                            })

                        # OPORTUNIDADE: Boa assimetria (>2x) e longe do alvo
                        elif assimetria >= 2 and progresso < 50:
                            cards.append({
                                'tipo': 'oportunidade',
                                'titulo': f'{ticker} com assimetria favorável',
                                'ticker': ticker,
                                'preco_atual': round(preco_atual, 2),
                                'preco_alvo': alvo,
                                'descricao': f'Assimetria risco/retorno de {assimetria:.1f}x. Vale o risco!',
                                'justificativa': f'Ganho potencial: {ganho_potencial:.1f}% | Risco: {risco:.1f}%',
                                'ganho_potencial': round(ganho_potencial, 2),
                                'acoes_sugeridas': [
                                    {'label': 'Simular compra', 'acao': 'simular_compra', 'ticker': ticker},
                                    {'label': 'Ver análise', 'acao': 'ver_ativo', 'ticker': ticker}
                                ],
                                'prioridade': 2,
                                'risco': 'medio'
                            })

                        # ALERTA: Stop atingido
                        if stop and preco_atual <= stop * 1.02:  # 2% de margem
                            cards.append({
                                'tipo': 'alerta',
                                'titulo': f'{ticker} próximo do stop!',
                                'ticker': ticker,
                                'preco_atual': round(preco_atual, 2),
                                'descricao': f'Preço em R$ {preco_atual:.2f}. Stop em R$ {stop:.2f}. Avalie sua posição.',
                                'justificativa': 'Proteção de capital é fundamental. Considere sair ou ajustar stop.',
                                'acoes_sugeridas': [
                                    {'label': 'Ver gráfico', 'acao': 'ver_grafico', 'ticker': ticker},
                                    {'label': 'Executar stop', 'acao': 'executar_stop'}
                                ],
                                'prioridade': 1,
                                'risco': 'alto'
                            })

                except Exception as e:
                    print(f"Erro ao buscar {ticker}: {e}")
                    continue

        except Exception as e:
            print(f"Erro na análise de watchlist: {e}")

        return cards

    def _analise_mercado(self) -> List[Dict]:
        """Detecta oportunidades de mercado"""
        cards = []

        try:
            # Analisa IBOV
            ibov = yf.Ticker('^BVSP')
            hist_ibov = ibov.history(period='5d')

            if len(hist_ibov) >= 2:
                variacao_ibov = ((hist_ibov['Close'].iloc[-1] - hist_ibov['Close'].iloc[-2]) / hist_ibov['Close'].iloc[-2] * 100)

                # Se IBOV caiu >2%, sugere oportunidade
                if variacao_ibov < -2:
                    cards.append({
                        'tipo': 'oportunidade',
                        'titulo': 'IBOVESPA em queda',
                        'descricao': f'IBOV caiu {abs(variacao_ibov):.2f}% hoje. Momento de buscar oportunidades.',
                        'justificativa': 'Quedas do mercado podem ser boas oportunidades de entrada em ativos de qualidade.',
                        'acoes_sugeridas': [
                            {'label': 'Ver ações em queda', 'acao': 'ver_oportunidades'},
                            {'label': 'Analisar watchlist', 'acao': 'watchlist'}
                        ],
                        'prioridade': 2,
                        'risco': 'medio'
                    })

                # Se IBOV subiu >2%, alerta para realização
                elif variacao_ibov > 2:
                    cards.append({
                        'tipo': 'alerta',
                        'titulo': 'IBOVESPA em alta',
                        'descricao': f'IBOV subiu {variacao_ibov:.2f}% hoje. Considere realizar lucros parciais.',
                        'justificativa': 'Altas expressivas são momentos para avaliar realização de lucros.',
                        'acoes_sugeridas': [
                            {'label': 'Ver portfolio', 'acao': 'portfolio'},
                            {'label': 'Rebalancear', 'acao': 'rebalancear'}
                        ],
                        'prioridade': 2,
                        'risco': 'baixo'
                    })

            # Analisa SELIC
            try:
                url_selic = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
                r = requests.get(url_selic, timeout=5)
                if r.status_code == 200:
                    data_selic = r.json()
                    if data_selic and len(data_selic) > 0:
                        selic = float(data_selic[0]['valor'])

                        if selic >= 10:
                            cards.append({
                                'tipo': 'oportunidade',
                                'titulo': f'SELIC a {selic}% a.a.',
                                'descricao': 'Renda Fixa atrativa! Considere CDBs 100%+ CDI.',
                                'justificativa': f'Com SELIC a {selic}%, CDBs pagam ~{selic*1.03:.2f}% a.a. líquido.',
                                'ganho_potencial': selic * 1.03,
                                'acoes_sugeridas': [
                                    {'label': 'Ver CDBs', 'acao': 'ver_cdb'},
                                    {'label': 'Simular RF', 'acao': 'simular_rf'}
                                ],
                                'prioridade': 3,
                                'risco': 'baixo'
                            })
            except:
                pass

        except Exception as e:
            print(f"Erro na análise de mercado: {e}")

        return cards

    def _analise_noticias(self) -> List[Dict]:
        """Analisa notícias com IA e gera alertas"""
        cards = []

        if not self.client:
            return cards

        try:
            # Cache de notícias (usa API do radar)
            import feedparser

            fontes = [
                "https://www.infomoney.com.br/feed/",
                "https://valor.globo.com/rss/home/"
            ]

            todas_noticias = []
            for url in fontes:
                try:
                    feed = feedparser.parse(url)
                    for entry in feed.entries[:3]:
                        todas_noticias.append(entry.get('title', ''))
                except:
                    continue

            if todas_noticias:
                # Analisa com IA
                noticias_texto = "\n".join([f"- {n}" for n in todas_noticias[:10]])

                prompt = f"""Analise as notícias abaixo e identifique UMA oportunidade ou alerta relevante para investidores:

NOTÍCIAS:
{noticias_texto}

Responda em JSON:
{{
  "relevante": true/false,
  "titulo": "título do card",
  "descricao": "descrição curta",
  "ticker": "ticker se aplicável ou null",
  "tipo": "oportunidade ou alerta"
}}

Se não houver nada relevante, retorne relevante: false."""

                completion = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Você é um analista financeiro. Responda sempre em JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )

                resposta = completion.choices[0].message.content

                # Parse JSON
                import re
                resposta = re.sub(r'```json\n?', '', resposta)
                resposta = re.sub(r'```\n?', '', resposta)

                resultado = json.loads(resposta)

                if resultado.get('relevante'):
                    cards.append({
                        'tipo': resultado.get('tipo', 'noticia'),
                        'titulo': resultado.get('titulo', 'Notícia relevante'),
                        'ticker': resultado.get('ticker'),
                        'descricao': resultado.get('descricao', ''),
                        'justificativa': 'Análise de IA baseada em notícias recentes.',
                        'acoes_sugeridas': [
                            {'label': 'Ver notícias', 'acao': 'ver_noticias'},
                            {'label': 'Analisar impacto', 'acao': 'analise_ia'}
                        ],
                        'prioridade': 2,
                        'risco': 'medio'
                    })

        except Exception as e:
            print(f"Erro na análise de notícias: {e}")

        return cards

    def _salvar_cards(self, cards: List[Dict]):
        """Salva cards no banco de dados"""
        try:
            # Limpa cards antigos (>24h)
            execute_query("DELETE FROM action_cards WHERE created_at < NOW() - INTERVAL '24 hours'")

            # Insere novos cards
            for card in cards:
                query = """
                    INSERT INTO action_cards
                    (tipo, titulo, descricao, ticker, preco_atual, preco_alvo, ganho_potencial,
                     risco, justificativa, acoes_sugeridas, prioridade, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() + INTERVAL '24 hours')
                """
                execute_query(query, (
                    card.get('tipo'),
                    card.get('titulo'),
                    card.get('descricao'),
                    card.get('ticker'),
                    card.get('preco_atual'),
                    card.get('preco_alvo'),
                    card.get('ganho_potencial'),
                    card.get('risco'),
                    card.get('justificativa'),
                    json.dumps(card.get('acoes_sugeridas', [])),
                    card.get('prioridade', 3)
                ))
        except Exception as e:
            print(f"Erro ao salvar cards: {e}")

    def gerar_briefing_diario(self) -> Dict[str, Any]:
        """Gera briefing diário com resumo de mercado + ações sugeridas"""
        try:
            # Gera cards primeiro
            cards = self.gerar_action_cards()

            # Busca dados de mercado
            ibov = yf.Ticker('^BVSP')
            hist_ibov = ibov.history(period='2d')
            var_ibov = 0
            if len(hist_ibov) >= 2:
                var_ibov = ((hist_ibov['Close'].iloc[-1] - hist_ibov['Close'].iloc[-2]) / hist_ibov['Close'].iloc[-2] * 100)

            # Busca USD/BRL
            usd_brl = 4.95
            try:
                url_usd = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
                r = requests.get(url_usd, timeout=5)
                if r.status_code == 200:
                    usd_brl = float(r.json()["USDBRL"]["bid"])
            except:
                pass

            # Monta briefing
            hora_atual = datetime.now()
            periodo = 'Manhã' if hora_atual.hour < 12 else 'Tarde' if hora_atual.hour < 18 else 'Noite'

            briefing = {
                "titulo": f"Briefing de {periodo} - {hora_atual.strftime('%d/%m/%Y')}",
                "conteudo": f"""
📊 **Mercado Hoje:**
- IBOVESPA: {'+' if var_ibov >= 0 else ''}{var_ibov:.2f}%
- USD/BRL: R$ {usd_brl:.2f}

🎯 **Ações Recomendadas:**
{self._formatar_cards_briefing(cards[:3])}

💡 **Dica do Dia:**
{self._gerar_dica_ia()}
                """.strip(),
                "timestamp": hora_atual.isoformat(),
                "categoria": "diario",
                "fonte": "mentor_ativo"
            }

            # Salva no banco
            query = """
                INSERT INTO briefings (titulo, conteudo, categoria, fonte)
                VALUES (%s, %s, %s, %s)
            """
            execute_query(query, (
                briefing['titulo'],
                briefing['conteudo'],
                briefing['categoria'],
                briefing['fonte']
            ))

            return briefing

        except Exception as e:
            print(f"Erro ao gerar briefing: {e}")
            return {
                "titulo": "Briefing do Dia",
                "conteudo": "Erro ao gerar briefing. Tente novamente mais tarde.",
                "timestamp": datetime.now().isoformat()
            }

    def _formatar_cards_briefing(self, cards: List[Dict]) -> str:
        """Formata cards para o briefing"""
        if not cards:
            return "- Nenhuma ação urgente no momento."

        linhas = []
        for i, card in enumerate(cards, 1):
            emoji = '🔔' if card['tipo'] == 'alerta' else '💰' if card['tipo'] == 'oportunidade' else '📈'
            linhas.append(f"{i}. {emoji} {card['titulo']}")

        return "\n".join(linhas)

    def _gerar_dica_ia(self) -> str:
        """Gera dica personalizada com IA"""
        if not self.client:
            return "Mantenha a disciplina e siga seu plano de investimentos."

        try:
            prompt = "Dê uma dica rápida (1 frase) sobre investimentos para um investidor brasileiro conservador/moderado."

            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=100
            )

            return completion.choices[0].message.content.strip()

        except:
            return "Diversificação é a chave para reduzir riscos e potencializar ganhos."
