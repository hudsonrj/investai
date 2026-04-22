function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
    
    document.getElementById(tabName).style.display = 'block';
    event.target.classList.add('active');
    
    if (tabName === 'portfolio') loadPortfolio();
    if (tabName === 'acoes') loadAcoes();
    if (tabName === 'cryptos') loadCryptos();
    if (tabName === 'watchlist') loadWatchlist();
}

async function loadPortfolio() {
    const res = await fetch('/api/portfolio/');
    const data = await res.json();
    const total = data.total || 0;
    const items = data.items || [];

    document.getElementById('portfolio-list').innerHTML = `
        <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <h3>💰 Total Geral</h3>
            <p style="font-size: 2em; font-weight: bold;">R$ ${total.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</p>
        </div>
        ${items.map(item =>
            `<div class="card">
                <h3>${item.produto}</h3>
                <p>Tipo: ${item.tipo}</p>
                <p>Instituição: ${item.instituicao}</p>
                <p><strong>Valor:</strong> R$ ${parseFloat(item.valor_atual).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</p>
                <p>Rentabilidade: ${item.rentabilidade_tipo} ${item.taxa_anual ? item.taxa_anual + '%' : ''}</p>
            </div>`
        ).join('')}
    `;
}

async function loadAcoes() {
    document.getElementById('acoes-list').innerHTML = '<p>Carregando ações...</p>';
}

async function loadCryptos() {
    const res = await fetch('/api/exchanges/binance/portfolio');
    const data = await res.json();
    document.getElementById('cryptos-list').innerHTML = `
        <p><strong>Total Binance:</strong> R$ ${data.total_brl.toFixed(2)}</p>
        ${data.items.map(item => 
            `<div class="card">
                <h3>${item.asset}</h3>
                <p>Total: ${item.total}</p>
                <p>Valor: R$ ${item.valor_brl.toFixed(2)}</p>
            </div>`
        ).join('')}
    `;
}

async function loadWatchlist() {
    const res = await fetch('/api/portfolio/watchlist');
    const data = await res.json();
    document.getElementById('watchlist-list').innerHTML = data.map(item => {
        const upside = item.alvo && item.entrada ? ((item.alvo - item.entrada) / item.entrada * 100).toFixed(2) : 0;
        return `<div class="card">
            <h3>${item.ticker} - ${item.nome}</h3>
            <p>Tipo: ${item.tipo}</p>
            <p>Entrada: R$ ${item.entrada ? item.entrada.toFixed(2) : '-'}</p>
            <p>Alvo: R$ ${item.alvo ? item.alvo.toFixed(2) : '-'} <span style="color: #4ade80;">(+${upside}%)</span></p>
            ${item.stop ? `<p>Stop: R$ ${item.stop.toFixed(2)}</p>` : ''}
            <p style="font-size: 0.9em; color: #94a3b8;">${item.observacoes || ''}</p>
        </div>`;
    }).join('');
}

// Carregar portfolio ao iniciar
document.addEventListener('DOMContentLoaded', () => {
    loadPortfolio();
});