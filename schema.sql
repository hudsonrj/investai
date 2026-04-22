-- InvestAI Database Schema
-- Portfolio Hudson R$395k + Watchlist + Binance

-- Portfolio principal (renda fixa + ações)
CREATE TABLE IF NOT EXISTS portfolio (
    id SERIAL PRIMARY KEY,
    produto TEXT NOT NULL,
    tipo TEXT NOT NULL,
    instituicao TEXT,
    valor_inicial NUMERIC(12,2) NOT NULL,
    valor_atual NUMERIC(12,2) NOT NULL,
    rentabilidade_tipo TEXT,
    taxa_anual NUMERIC(5,2),
    liquidez TEXT,
    vencimento DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Watchlist de ativos para monitorar
CREATE TABLE IF NOT EXISTS watchlist (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    nome TEXT,
    tipo TEXT,
    entrada NUMERIC(10,2),
    alvo NUMERIC(10,2),
    stop NUMERIC(10,2),
    quantidade INTEGER,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Portfolio Binance (cryptos)
CREATE TABLE IF NOT EXISTS portfolio_binance (
    id SERIAL PRIMARY KEY,
    asset TEXT NOT NULL,
    free NUMERIC(20,8),
    locked NUMERIC(20,8),
    total NUMERIC(20,8),
    preco_brl NUMERIC(12,2),
    valor_brl NUMERIC(12,2),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Cotações gerais
CREATE TABLE IF NOT EXISTS cotacoes (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    fonte TEXT NOT NULL,
    preco NUMERIC(12,6),
    variacao_24h NUMERIC(8,4),
    volume_24h NUMERIC(20,2),
    market_cap NUMERIC(20,2),
    timestamp TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, fonte, timestamp)
);

-- Metas financeiras
CREATE TABLE IF NOT EXISTS metas (
    id SERIAL PRIMARY KEY,
    objetivo TEXT NOT NULL,
    valor_alvo NUMERIC(12,2) NOT NULL,
    prazo_meses INTEGER,
    prioridade INTEGER DEFAULT 3,
    status TEXT DEFAULT 'ativa',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Cenários de investimento
CREATE TABLE IF NOT EXISTS cenarios (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT,
    perfil TEXT,
    alocacao_json JSONB,
    projecao_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sugestões da IA
CREATE TABLE IF NOT EXISTS sugestoes (
    id SERIAL PRIMARY KEY,
    tipo TEXT NOT NULL,
    ticker TEXT,
    preco_atual NUMERIC(12,2),
    preco_alvo NUMERIC(12,2),
    justificativa TEXT,
    risco TEXT,
    horizonte TEXT,
    status TEXT DEFAULT 'nova',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Briefings diários
CREATE TABLE IF NOT EXISTS briefings (
    id SERIAL PRIMARY KEY,
    titulo TEXT NOT NULL,
    conteudo TEXT,
    categoria TEXT,
    fonte TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Histórico de preços
CREATE TABLE IF NOT EXISTS historico_precos (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    data DATE NOT NULL,
    abertura NUMERIC(12,6),
    maximo NUMERIC(12,6),
    minimo NUMERIC(12,6),
    fechamento NUMERIC(12,6),
    volume BIGINT,
    UNIQUE(ticker, data)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_cotacoes_ticker ON cotacoes(ticker);
CREATE INDEX IF NOT EXISTS idx_cotacoes_timestamp ON cotacoes(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_watchlist_ticker ON watchlist(ticker);
CREATE INDEX IF NOT EXISTS idx_historico_ticker_data ON historico_precos(ticker, data DESC);

-- Inserir portfolio Hudson (R$ 395k)
INSERT INTO portfolio (produto, tipo, instituicao, valor_inicial, valor_atual, rentabilidade_tipo, taxa_anual, liquidez) VALUES
('LCI 94% CDI', 'Renda Fixa', 'Banco Inter', 120000.00, 120000.00, 'CDI', 94.00, 'D+90'),
('CDB 103% CDI', 'Renda Fixa', 'BTG Pactual', 180000.00, 180000.00, 'CDI', 103.00, 'Vencimento'),
('VGBL 100% CDI', 'Previdência', 'Bradesco Vida', 80000.00, 80000.00, 'CDI', 100.00, 'Resgate'),
('ELET3', 'Ações', 'B3', 15000.00, 15000.00, 'Variável', NULL, 'D+2')
ON CONFLICT DO NOTHING;

-- Inserir watchlist Hudson
INSERT INTO watchlist (ticker, nome, tipo, entrada, alvo, stop, observacoes) VALUES
('SUZB3', 'Suzano', 'Ação', 47.49, 56.99, 42.74, 'Queda 6.25% em 08/04/2026'),
('TEND3', 'Tenda', 'Ação', 29.26, 38.00, 23.41, 'Assimetria 1.49x'),
('HGBS11', 'HGBS11', 'FII', 20.48, 26.00, NULL, 'DY 9.96%'),
('ELET3', 'Eletrobras', 'Ação', 59.37, 75.00, 47.50, 'Privatização'),
('KNSC11', 'KNSC11', 'FII', 9.02, 10.50, NULL, 'DY 12.64%'),
('PRIO3', 'PetroRio', 'Ação', 67.49, 74.00, 53.99, 'Assimetria 0.43x')
ON CONFLICT DO NOTHING;
