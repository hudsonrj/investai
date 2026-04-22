# InvestAI — Plataforma de Investimentos com IA

Plataforma financeira 360° com agentes de IA proativos, dados de mercado em tempo real e simulador de cenários de investimento.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Redis](https://img.shields.io/badge/Redis-7-red)

---

## Funcionalidades

| Módulo | Descrição |
|---|---|
| **Dashboard** | Painel principal com portfolio, ações B3, cryptos e watchlist |
| **Cenários** | Simulador de alocação: Atual / Conservador / Moderado / Arrojado |
| **Plano de Ação** | Guia passo a passo com checklists e simulador SELIC |
| **Radar de Mercado** | Índices globais ao vivo + notícias + análise de IA |
| **Smart Money** | Volume anômalo, insider tracking (B3 + SEC Form 4) |
| **Chat IA** | Assistente flutuante contextual (Groq / LLaMA 3.3 70B) |
| **Mentor Ativo** | Action cards proativos gerados por IA com base no portfolio |
| **Ticker Tape** | Fita de cotações em tempo real no topo de todas as páginas |

---

## Arquitetura

```
investai/
├── api/
│   ├── main.py              # FastAPI app, routers, scheduler de feeds
│   ├── database.py          # PostgreSQL + Redis helpers
│   ├── middleware/
│   │   └── auth_middleware.py  # JWT via HttpOnly cookie
│   └── routers/
│       ├── auth.py          # Login / logout / /me
│       ├── portfolio.py     # Portfolio + watchlist enriquecida com yfinance
│       ├── exchanges.py     # Cryptos (CoinGecko), Ações B3/INT, Renda Fixa, Moedas, Ticker-Tape
│       ├── radar.py         # Índices globais (yfinance) + notícias RSS + análise IA
│       ├── smartmoney.py    # Volume anômalo, insider tracker, análise IA
│       ├── cenarios.py      # Cenários de rebalanceamento ML
│       ├── sugestoes.py     # Action cards (Mentor Ativo)
│       ├── chat.py          # Chat contextual com Orchestrator
│       ├── chat_proativo.py # Insights proativos via polling
│       ├── historico.py     # Histórico de portfolio
│       └── plano.py         # Plano de ação por perfil
├── agents/
│   ├── orchestrator.py      # Coordenador multi-agente + APScheduler
│   └── suggestion_engine.py # Motor de sugestões: portfolio + watchlist + mercado + notícias
├── ml/
│   └── cenarios.py          # Geração de cenários Conservador/Moderado/Arrojado
├── feeds/
│   ├── moedas.py            # Atualiza cotações de moedas a cada 5 min
│   ├── binance.py           # Sincroniza portfolio Binance a cada 10 min
│   └── acoes_b3.py          # Atualiza preços B3 a cada 15 min
├── core/
│   └── brokers.py           # Mapa de corretoras e produtos por categoria
├── dashboard/               # HTML das páginas (sem framework JS)
│   ├── index.html           # Painel principal
│   ├── cenarios.html        # Simulador de cenários
│   ├── plano.html           # Plano de ação
│   ├── noticias.html        # Radar de mercado
│   ├── smartmoney.html      # Smart Money tracker
│   ├── login.html           # Tela de autenticação
│   ├── auth-guard.js        # Guard de autenticação JWT
│   └── chat-widget.js       # Widget de chat flutuante
├── static/
│   ├── style.css            # Design system Bloomberg-style (dark navy)
│   └── app-v2.js            # JS do dashboard principal
├── migrations/              # Scripts SQL de evolução do schema
├── schema.sql               # Schema completo do banco de dados
├── requirements.txt         # Dependências Python
├── docker-compose.yml       # PostgreSQL + Redis via Docker
├── ecosystem.config.js      # Configuração PM2
└── .env.example             # Variáveis de ambiente (modelo)
```

---

## Fontes de Dados

| Dado | Fonte | Cache |
|---|---|---|
| Cryptos (BTC/ETH/BNB/SOL/XRP…) | [CoinGecko API](https://www.coingecko.com/en/api) (free) | 2 min |
| Ações B3 (PETR4/VALE3/ITUB4…) | yfinance | 5 min |
| Ações EUA (AAPL/MSFT/NVDA…) | yfinance | 5 min |
| Índices globais (IBOV/S&P/NASDAQ…) | yfinance | 5 min |
| Moedas (USD/EUR/GBP…) | [open.er-api.com](https://www.exchangerate-api.com/) (free) | 15 min |
| SELIC | [BCB API](https://api.bcb.gov.br/) (oficial) | 1 hora |
| Notícias | RSS (InfoMoney, G1, Folha, Valor, Yahoo) | 15 min |
| Portfolio Binance | Binance REST API | 10 min |
| Análise IA | [Groq](https://console.groq.com/) — LLaMA 3.3 70B | 30 min |

---

## Requisitos

- Python 3.12+
- PostgreSQL 15 (porta 5435)
- Redis 7 (porta 6380)
- Docker + Docker Compose (para subir banco e Redis)
- PM2 (para gerenciar o processo em produção)

---

## Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/hudsonrj/investai.git
cd investai
```

### 2. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite .env com suas chaves de API e credenciais
```

### 3. Suba PostgreSQL + Redis com Docker
```bash
docker-compose up -d
```

### 4. Instale dependências Python
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Crie o schema do banco
```bash
psql -h localhost -p 5435 -U investai -d investai -f schema.sql
psql -h localhost -p 5435 -U investai -d investai -f migrations/001_action_cards.sql
psql -h localhost -p 5435 -U investai -d investai -f migrations/002_carteira_recomendada.sql
psql -h localhost -p 5435 -U investai -d investai -f migrations/003_plano_investimento.sql
psql -h localhost -p 5435 -U investai -d investai -f migrations/004_smart_money.sql
```

### 6. Inicie o servidor

**Com PM2 (produção):**
```bash
pm2 start ecosystem.config.js
pm2 save
```

**Direto (desenvolvimento):**
```bash
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8091 --reload
```

Acesse: `http://localhost:8091`

---

## API — Endpoints principais

### Autenticação
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/auth/login` | Login (retorna JWT em cookie HttpOnly) |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Dados do usuário autenticado |

### Portfolio
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/portfolio/` | Portfolio completo (RF + RV + Previdência) |
| GET | `/api/portfolio/watchlist` | Watchlist enriquecida com preço atual + semáforo |
| GET | `/api/portfolio/binance` | Portfolio Binance sincronizado |

### Mercado
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/exchanges/cryptos` | 15 criptomoedas (BRL + USD + variação 24h) |
| GET | `/api/exchanges/acoes-b3` | 15 ações B3 com variação |
| GET | `/api/exchanges/acoes-int` | 8 ações americanas |
| GET | `/api/exchanges/renda-fixa` | SELIC, CDI, CDB, LCI, LCA, Tesouro |
| GET | `/api/exchanges/moedas-expandido` | 8 pares de moedas vs BRL |
| GET | `/api/exchanges/ticker-tape` | Feed combinado para fita de cotações |
| GET | `/api/radar/mercados` | 10 índices globais (IBOV, S&P, NASDAQ…) |
| GET | `/api/radar/noticias` | Últimas 35 notícias financeiras |
| GET | `/api/radar/analise` | Análise IA do mercado (otimista/neutro/pessimista) |

### Smart Money
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/smartmoney/volume-anomalias` | Ativos com volume > 1.5x média 30d |
| GET | `/api/smartmoney/insider-tracker` | Fatos Relevantes B3 + SEC Form 4 |
| GET | `/api/smartmoney/analise-ia` | Análise IA de movimentos institucionais |

### IA / Chat
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/chat/context` | Chat contextual com dados do portfolio |
| GET | `/api/chat/proativo` | Consulta insight proativo pendente |
| POST | `/api/chat/proativo/gerar` | Gera novo insight proativo |
| POST | `/api/chat/proativo/limpar` | Marca insight como lido |

---

## Design System

O frontend usa um design system próprio inspirado em Bloomberg Terminal / TradingView.

**Paleta principal:**
```css
--bg-primary:  #0a0e1a   /* Navy escuro */
--bg-card:     #141b2d   /* Cards */
--accent:      #00d4ff   /* Ciano — destaque */
--gain:        #00c853   /* Verde — ganho */
--loss:        #ff3d57   /* Vermelho — perda */
--warning:     #ffb300   /* Âmbar — alerta */
```

**Componentes disponíveis em `static/style.css`:**
- `.ticker-tape` — fita de cotações animada
- `.data-table` — tabelas financeiras com zebra
- `.cenarios-comparison` — comparativo de 4 colunas
- `.selic-simulator` — simulador interativo
- `.whale-alert`, `.insider-card` — Smart Money
- `.action-card` — cards proativos do Mentor Ativo
- `.watchlist-row` com semáforo colorido
- `.accordion`, `.stepper`, `.checklist-item` — Plano de Ação

---

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `GROQ_API_KEY` | Sim | Chave da API Groq (chat IA e análises) |
| `POSTGRES_*` | Sim | Credenciais do PostgreSQL |
| `REDIS_*` | Sim | Credenciais do Redis |
| `JWT_SECRET` | Sim | Segredo para assinar tokens JWT (min. 32 chars) |
| `AUTH_USERNAME` | Sim | Usuário de acesso à plataforma |
| `AUTH_PASSWORD` | Sim | Senha de acesso |
| `BINANCE_API_KEY` | Não | Para sincronizar portfolio Binance real |
| `BINANCE_API_SECRET` | Não | Para sincronizar portfolio Binance real |

---

## Licença

Projeto privado — Hudson RJ © 2026
