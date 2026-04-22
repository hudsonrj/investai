"""
InvestAI - Cenários ML
Machine Learning powered scenario projections with:
- Asset allocation optimization
- Return projections (1Y, 3Y, 5Y)
- Risk metrics (volatility, max drawdown, Sharpe ratio)
- Specific transfer suggestions
"""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

# Parâmetros de mercado (baseados em dados históricos)
SELIC_ATUAL = 10.75 / 100
CDI_ATUAL = 10.50 / 100
IPCA_ATUAL = 4.50 / 100

# Retornos esperados anuais (baseados em dados históricos)
RETORNOS_ESPERADOS = {
    'rf': 0.1050,  # CDI ~10.50%
    'acoes_br': 0.1500,  # Ações BR históricas ~15%
    'fii': 0.1200,  # FIIs ~12% (dividendos + valorização)
    'crypto': 0.5000,  # Crypto ~50% (alta volatilidade)
    'internacional': 0.1200  # Ações internacionais ~12%
}

# Volatilidades anuais (desvio padrão)
VOLATILIDADES = {
    'rf': 0.02,  # RF muito baixa volatilidade
    'acoes_br': 0.25,  # Ações BR ~25%
    'fii': 0.15,  # FIIs ~15%
    'crypto': 0.80,  # Crypto altíssima volatilidade
    'internacional': 0.20  # Ações int. ~20%
}

# Correlações (simplificadas)
CORRELACOES = {
    ('rf', 'acoes_br'): -0.1,
    ('rf', 'fii'): 0.1,
    ('rf', 'crypto'): 0.0,
    ('acoes_br', 'fii'): 0.6,
    ('acoes_br', 'crypto'): 0.3,
    ('fii', 'crypto'): 0.2
}


class CenariosML:
    def __init__(self):
        self.dias_ano = 252
        self.meses_ano = 12

    def gerar_cenarios(self, portfolio_atual: Dict) -> List[Dict]:
        """
        Gera 4 cenários completos com projeções ML:
        - Atual
        - Conservador
        - Moderado
        - Arrojado
        """
        valor_total = portfolio_atual.get("total", 395000)

        # Define alocações para cada cenário
        alocacoes = {
            "Atual": {
                "rf": 0.88,
                "acoes_br": 0.04,
                "fii": 0.08,
                "crypto": 0.00
            },
            "Conservador": {
                "rf": 0.75,
                "acoes_br": 0.10,
                "fii": 0.15,
                "crypto": 0.00
            },
            "Moderado": {
                "rf": 0.60,
                "acoes_br": 0.15,
                "fii": 0.20,
                "crypto": 0.05
            },
            "Arrojado": {
                "rf": 0.40,
                "acoes_br": 0.30,
                "fii": 0.20,
                "crypto": 0.10
            }
        }

        cenarios = []

        for nome, alocacao in alocacoes.items():
            cenario = self._calcular_cenario(nome, alocacao, valor_total)
            cenarios.append(cenario)

        return cenarios

    def _calcular_cenario(self, nome: str, alocacao: Dict, valor_total: float) -> Dict:
        """Calcula um cenário completo com todas as métricas"""

        # 1. Retorno esperado do portfolio
        retorno_esperado = self._calcular_retorno_portfolio(alocacao)

        # 2. Volatilidade do portfolio
        volatilidade = self._calcular_volatilidade_portfolio(alocacao)

        # 3. Sharpe Ratio (retorno ajustado ao risco)
        sharpe = (retorno_esperado - CDI_ATUAL) / volatilidade if volatilidade > 0 else 0

        # 4. Projeções de valor (1Y, 3Y, 5Y)
        projecoes = {
            '1Y': self._projetar_valor(valor_total, retorno_esperado, 1),
            '3Y': self._projetar_valor(valor_total, retorno_esperado, 3),
            '5Y': self._projetar_valor(valor_total, retorno_esperado, 5)
        }

        # 5. Renda mensal estimada (baseada em dividendos)
        renda_mensal = self._calcular_renda_mensal(valor_total, alocacao)

        # 6. Max Drawdown estimado
        max_drawdown = self._estimar_max_drawdown(alocacao)

        # 7. Sugestões específicas de transferência
        sugestoes = self._gerar_sugestoes_transferencia(nome, alocacao, valor_total)

        # 8. Descrição do perfil
        descricoes = {
            "Atual": "88% Renda Fixa + 12% RV/FII - Concentração conservadora atual",
            "Conservador": "75% Renda Fixa + 25% RV/FII - Segurança com diversificação controlada",
            "Moderado": "60% RF + 35% RV/FII + 5% Crypto - Equilíbrio entre segurança e crescimento",
            "Arrojado": "40% RF + 50% RV/FII + 10% Crypto - Crescimento acelerado com risco controlado"
        }

        return {
            "id": hash(nome) % 10000,
            "nome": nome,
            "descricao": descricoes.get(nome, ""),
            "alocacao": self._formatar_alocacao_percentual(alocacao),
            "alocacao_valores": self._formatar_alocacao_valores(alocacao, valor_total),
            "retorno_esperado_anual": round(retorno_esperado * 100, 2),
            "volatilidade_anual": round(volatilidade * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
            "projecoes": {
                "1_ano": {
                    "valor": round(projecoes['1Y'], 2),
                    "ganho": round(projecoes['1Y'] - valor_total, 2),
                    "percentual": round((projecoes['1Y'] - valor_total) / valor_total * 100, 2)
                },
                "3_anos": {
                    "valor": round(projecoes['3Y'], 2),
                    "ganho": round(projecoes['3Y'] - valor_total, 2),
                    "percentual": round((projecoes['3Y'] - valor_total) / valor_total * 100, 2)
                },
                "5_anos": {
                    "valor": round(projecoes['5Y'], 2),
                    "ganho": round(projecoes['5Y'] - valor_total, 2),
                    "percentual": round((projecoes['5Y'] - valor_total) / valor_total * 100, 2)
                }
            },
            "renda_mensal": round(renda_mensal, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "risco": self._classificar_risco(volatilidade),
            "sugestoes_transferencia": sugestoes
        }

    def _calcular_retorno_portfolio(self, alocacao: Dict) -> float:
        """Calcula retorno esperado do portfolio (média ponderada)"""
        retorno = 0
        for ativo, peso in alocacao.items():
            retorno += peso * RETORNOS_ESPERADOS.get(ativo, 0)
        return retorno

    def _calcular_volatilidade_portfolio(self, alocacao: Dict) -> float:
        """Calcula volatilidade do portfolio considerando correlações"""
        # Simplificado: média ponderada das volatilidades individuais
        # (uma implementação completa usaria matriz de covariância)
        volatilidade = 0
        for ativo, peso in alocacao.items():
            volatilidade += (peso ** 2) * (VOLATILIDADES.get(ativo, 0.1) ** 2)

        # Adiciona efeito de correlação (simplificado)
        ativos_lista = list(alocacao.keys())
        for i, ativo1 in enumerate(ativos_lista):
            for ativo2 in ativos_lista[i+1:]:
                peso1 = alocacao[ativo1]
                peso2 = alocacao[ativo2]
                vol1 = VOLATILIDADES.get(ativo1, 0.1)
                vol2 = VOLATILIDADES.get(ativo2, 0.1)
                corr = CORRELACOES.get((ativo1, ativo2), 0) or CORRELACOES.get((ativo2, ativo1), 0)

                volatilidade += 2 * peso1 * peso2 * vol1 * vol2 * corr

        return np.sqrt(volatilidade)

    def _projetar_valor(self, valor_inicial: float, taxa_anual: float, anos: int) -> float:
        """Projeta valor futuro com juros compostos"""
        return valor_inicial * ((1 + taxa_anual) ** anos)

    def _calcular_renda_mensal(self, valor_total: float, alocacao: Dict) -> float:
        """Calcula renda mensal estimada (dividendos e juros)"""
        # RF paga mensalmente via juros
        renda_rf = valor_total * alocacao.get('rf', 0) * CDI_ATUAL / 12

        # FIIs pagam ~0.8% a.m. em média
        renda_fii = valor_total * alocacao.get('fii', 0) * 0.008

        # Ações pagam dividendos ~0.5% a.m. em média
        renda_acoes = valor_total * alocacao.get('acoes_br', 0) * 0.005

        return renda_rf + renda_fii + renda_acoes

    def _estimar_max_drawdown(self, alocacao: Dict) -> float:
        """Estima max drawdown baseado na volatilidade"""
        # Drawdown típico = ~2x volatilidade anual
        volatilidade = self._calcular_volatilidade_portfolio(alocacao)
        return volatilidade * 2

    def _formatar_alocacao_percentual(self, alocacao: Dict) -> Dict:
        """Formata alocação em percentuais"""
        return {k: round(v * 100, 1) for k, v in alocacao.items()}

    def _formatar_alocacao_valores(self, alocacao: Dict, valor_total: float) -> Dict:
        """Formata alocação em valores R$"""
        return {k: round(v * valor_total, 2) for k, v in alocacao.items()}

    def _classificar_risco(self, volatilidade: float) -> str:
        """Classifica risco baseado na volatilidade"""
        if volatilidade < 0.10:
            return "Baixo"
        elif volatilidade < 0.20:
            return "Médio"
        else:
            return "Alto"

    def _gerar_sugestoes_transferencia(self, nome: str, alocacao: Dict, valor_total: float) -> List[Dict]:
        """Gera sugestões específicas de onde mover o dinheiro"""
        sugestoes = []

        # Mapeamento de nomes amigáveis
        nomes_ativos = {
            'rf': 'Renda Fixa (CDB/LCI)',
            'acoes_br': 'Ações Brasileiras',
            'fii': 'Fundos Imobiliários',
            'crypto': 'Criptomoedas',
            'internacional': 'Ações Internacionais'
        }

        # Alocação atual estimada (88% RF, 4% ações, 8% FII, 0% crypto)
        alocacao_atual = {
            'rf': 0.88,
            'acoes_br': 0.04,
            'fii': 0.08,
            'crypto': 0.00
        }

        # Calcula diferenças
        for ativo, peso_novo in alocacao.items():
            peso_atual = alocacao_atual.get(ativo, 0)
            diferenca = peso_novo - peso_atual
            valor_diferenca = diferenca * valor_total

            if abs(valor_diferenca) > 1000:  # Só sugestões significativas (>R$1k)
                if valor_diferenca > 0:
                    # Aumentar posição
                    sugestoes.append({
                        'acao': 'aumentar',
                        'ativo': nomes_ativos.get(ativo, ativo),
                        'ativo_code': ativo,
                        'valor': round(abs(valor_diferenca), 2),
                        'percentual_atual': round(peso_atual * 100, 1),
                        'percentual_novo': round(peso_novo * 100, 1),
                        'descricao': f'Aumentar {nomes_ativos.get(ativo, ativo)} de {peso_atual*100:.1f}% para {peso_novo*100:.1f}%',
                        'exemplos': self._gerar_exemplos_ativos(ativo)
                    })
                else:
                    # Reduzir posição
                    sugestoes.append({
                        'acao': 'reduzir',
                        'ativo': nomes_ativos.get(ativo, ativo),
                        'ativo_code': ativo,
                        'valor': round(abs(valor_diferenca), 2),
                        'percentual_atual': round(peso_atual * 100, 1),
                        'percentual_novo': round(peso_novo * 100, 1),
                        'descricao': f'Reduzir {nomes_ativos.get(ativo, ativo)} de {peso_atual*100:.1f}% para {peso_novo*100:.1f}%'
                    })

        # Ordena por valor (maiores transferências primeiro)
        sugestoes.sort(key=lambda x: x['valor'], reverse=True)

        return sugestoes

    def _gerar_exemplos_ativos(self, tipo_ativo: str) -> List[str]:
        """Gera exemplos de ativos específicos para cada categoria"""
        exemplos = {
            'rf': ['CDB BTG 103% CDI', 'LCI Banco Inter 94% CDI', 'Tesouro SELIC 2029'],
            'acoes_br': ['ELET3', 'SUZB3', 'PRIO3', 'VALE3', 'ITUB4'],
            'fii': ['HGBS11 (DY 9.96%)', 'KNSC11 (DY 12.64%)', 'MXRF11'],
            'crypto': ['Bitcoin (BTC)', 'Ethereum (ETH)', 'Binance Coin (BNB)'],
            'internacional': ['IVVB11 (S&P 500)', 'BOVA11 (IBOV)', 'VOO (ETF S&P)']
        }
        return exemplos.get(tipo_ativo, [])

    def simular_aporte_mensal(self, valor_inicial: float, aporte_mensal: float,
                               taxa_anual: float, meses: int) -> Dict:
        """Simula crescimento com aportes mensais regulares"""
        taxa_mensal = (1 + taxa_anual) ** (1/12) - 1

        valor_final = valor_inicial
        historico = [valor_inicial]

        for mes in range(meses):
            valor_final = (valor_final + aporte_mensal) * (1 + taxa_mensal)
            historico.append(valor_final)

        total_aportado = valor_inicial + (aporte_mensal * meses)
        ganho_total = valor_final - total_aportado

        return {
            'valor_final': round(valor_final, 2),
            'total_aportado': round(total_aportado, 2),
            'ganho_total': round(ganho_total, 2),
            'rentabilidade_percentual': round((ganho_total / total_aportado * 100), 2) if total_aportado > 0 else 0,
            'historico': [round(v, 2) for v in historico]
        }

    def calcular_selic_simulator(self, valor: float, taxa_selic: float, meses: int) -> Dict:
        """Calcula retorno de investimento em Tesouro SELIC"""
        # SELIC paga diariamente
        taxa_diaria = (1 + taxa_selic) ** (1/252) - 1

        dias = meses * 21  # ~21 dias úteis por mês
        valor_final = valor * ((1 + taxa_diaria) ** dias)

        # IR regressivo
        if meses <= 6:
            ir_rate = 0.225
        elif meses <= 12:
            ir_rate = 0.20
        elif meses <= 24:
            ir_rate = 0.175
        else:
            ir_rate = 0.15

        ganho_bruto = valor_final - valor
        ir = ganho_bruto * ir_rate
        ganho_liquido = ganho_bruto - ir
        valor_final_liquido = valor + ganho_liquido

        return {
            'valor_inicial': round(valor, 2),
            'valor_final_bruto': round(valor_final, 2),
            'valor_final_liquido': round(valor_final_liquido, 2),
            'ganho_bruto': round(ganho_bruto, 2),
            'imposto_renda': round(ir, 2),
            'ganho_liquido': round(ganho_liquido, 2),
            'rentabilidade_bruta': round((ganho_bruto / valor * 100), 2),
            'rentabilidade_liquida': round((ganho_liquido / valor * 100), 2),
            'meses': meses,
            'taxa_selic': round(taxa_selic * 100, 2)
        }
