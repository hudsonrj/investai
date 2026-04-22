-- InvestAI - Carteira Recomendada Table
-- Stores AI-recommended portfolio allocations

CREATE TABLE IF NOT EXISTS carteira_recomendada (
    id SERIAL PRIMARY KEY,
    perfil TEXT NOT NULL, -- 'conservador', 'moderado', 'arrojado'
    alocacao JSONB NOT NULL, -- {"rf": 60, "rv": 25, "fii": 10, "crypto": 5}
    justificativa TEXT,
    ativos_sugeridos JSONB, -- Lista de ativos específicos por categoria
    valor_total_sugerido NUMERIC(12,2),
    rebalanceamento_necessario JSONB, -- Movimentações sugeridas
    valido_ate TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_carteira_perfil ON carteira_recomendada(perfil);
CREATE INDEX IF NOT EXISTS idx_carteira_created ON carteira_recomendada(created_at DESC);
