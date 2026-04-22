-- InvestAI - Smart Money Tables
-- Stores insider trading and volume anomaly tracking

CREATE TABLE IF NOT EXISTS volume_anomalias (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    volume_atual BIGINT,
    volume_medio BIGINT,
    razao NUMERIC(8,2), -- volume_atual / volume_medio
    tipo TEXT, -- 'elevado', 'alta_anomala', 'baixo'
    preco_atual NUMERIC(12,2),
    variacao_dia NUMERIC(8,2),
    data DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, data)
);

CREATE TABLE IF NOT EXISTS insider_movements (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    empresa TEXT,
    tipo TEXT NOT NULL, -- 'compra', 'venda', 'fato_relevante'
    insider_nome TEXT,
    quantidade INTEGER,
    valor_total NUMERIC(12,2),
    fonte TEXT, -- 'b3', 'sec', 'cvm'
    link TEXT,
    data_movimento DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS baleia_alerts (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    tipo_alerta TEXT NOT NULL, -- 'volume_spike', 'insider_buy', 'insider_sell'
    descricao TEXT,
    severidade INTEGER DEFAULT 2, -- 1=crítico, 2=alto, 3=médio
    dados JSONB,
    notificado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_volume_ticker_data ON volume_anomalias(ticker, data DESC);
CREATE INDEX IF NOT EXISTS idx_insider_ticker ON insider_movements(ticker);
CREATE INDEX IF NOT EXISTS idx_insider_data ON insider_movements(data_movimento DESC);
CREATE INDEX IF NOT EXISTS idx_baleia_ticker ON baleia_alerts(ticker);
CREATE INDEX IF NOT EXISTS idx_baleia_created ON baleia_alerts(created_at DESC);
