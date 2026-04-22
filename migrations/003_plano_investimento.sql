-- InvestAI - Plano de Investimento Tables
-- Stores investment plan data for step-by-step guide

CREATE TABLE IF NOT EXISTS plano_perfil (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    perfil TEXT NOT NULL, -- 'conservador', 'moderado', 'arrojado'
    objetivos JSONB, -- Lista de objetivos
    horizonte_meses INTEGER,
    capital_inicial NUMERIC(12,2),
    aporte_mensal NUMERIC(12,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS plano_checklist (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    plano_id INTEGER REFERENCES plano_perfil(id),
    item TEXT NOT NULL,
    categoria TEXT, -- 'perfil', 'objetivos', 'alocacao', 'execucao'
    concluido BOOLEAN DEFAULT FALSE,
    data_conclusao TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_plano_user ON plano_perfil(user_id);
CREATE INDEX IF NOT EXISTS idx_checklist_user ON plano_checklist(user_id);
CREATE INDEX IF NOT EXISTS idx_checklist_plano ON plano_checklist(plano_id);
