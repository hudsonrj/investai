-- InvestAI - Action Cards Table
-- Stores AI-generated action cards for proactive suggestions

CREATE TABLE IF NOT EXISTS action_cards (
    id SERIAL PRIMARY KEY,
    tipo TEXT NOT NULL, -- 'oportunidade', 'alerta', 'rebalanceamento', 'noticia'
    titulo TEXT NOT NULL,
    descricao TEXT,
    ticker TEXT,
    preco_atual NUMERIC(12,2),
    preco_alvo NUMERIC(12,2),
    ganho_potencial NUMERIC(8,2),
    risco TEXT, -- 'baixo', 'medio', 'alto'
    justificativa TEXT,
    acoes_sugeridas JSONB, -- Lista de botões de ação
    prioridade INTEGER DEFAULT 3, -- 1=alta, 2=media, 3=baixa
    status TEXT DEFAULT 'ativa', -- 'ativa', 'executada', 'descartada', 'expirada'
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_action_cards_status ON action_cards(status);
CREATE INDEX IF NOT EXISTS idx_action_cards_created ON action_cards(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_action_cards_prioridade ON action_cards(prioridade);
