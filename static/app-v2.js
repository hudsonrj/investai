// ═══════════════════════════════════════════════════════════════════════════
//  InvestAI v3.0 — Professional Finance Dashboard
// ═══════════════════════════════════════════════════════════════════════════

// ── Formatters ──────────────────────────────────────────────────────────────
const fmtBRL = (v, dec = 2) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: dec, maximumFractionDigits: dec }).format(v);

const fmtBRLCompact = (v) => {
  if (v >= 1e6) return `R$ ${(v / 1e6).toFixed(2)}M`;
  if (v >= 1e3) return `R$ ${(v / 1e3).toFixed(1)}k`;
  return fmtBRL(v);
};

const fmtPct = (v, forceSign = true) => {
  const sign = forceSign && v > 0 ? '+' : '';
  return `${sign}${v.toFixed(2)}%`;
};

const fmtNum = (v) => new Intl.NumberFormat('pt-BR').format(v);

const changeClass = (v) => v >= 0 ? 'positive' : 'negative';
const changeArrow = (v) => v >= 0 ? '▲' : '▼';

function priceChangeSpan(pct) {
  const cls = changeClass(pct);
  return `<span class="price-change ${cls}">${changeArrow(pct)} ${fmtPct(pct)}</span>`;
}

function priceBadge(pct) {
  const cls = changeClass(pct);
  return `<span class="price-badge ${cls}">${changeArrow(pct)} ${fmtPct(pct)}</span>`;
}

// ── Ticker watchlist data ────────────────────────────────────────────────────
const TICKER_INFO = {
  'PRIO3': { entrada: 58.20, alvo: 70.00, stop: 52.38 },
  'TEND3': { entrada: 8.50,  alvo: 10.20, stop: 7.65  },
  'KNSC11':{ entrada: 103.50,alvo: 115.00,stop: 93.15 },
  'HGBS11':{ entrada: 98.75, alvo: 110.00,stop: 88.88 },
  'ELET3': { entrada: 59.37, alvo: 71.24, stop: 53.40 },
  'SUZB3': { entrada: 47.49, alvo: 56.99, stop: 42.74 },
};

// ── Clock ────────────────────────────────────────────────────────────────────
function startClock() {
  const timeEl = document.getElementById('clock-time');
  const dateEl = document.getElementById('clock-date');
  const statusDot = document.getElementById('market-status-dot');
  const statusTxt = document.getElementById('market-status-text');
  if (!timeEl) return;

  function tick() {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2,'0');
    const mm = String(now.getMinutes()).padStart(2,'0');
    const ss = String(now.getSeconds()).padStart(2,'0');
    timeEl.textContent = `${hh}:${mm}:${ss}`;
    if (dateEl) dateEl.textContent = now.toLocaleDateString('pt-BR');

    // B3 open hours: weekdays 10:00-17:55 BRT (UTC-3)
    const utcH = now.getUTCHours();
    const utcM = now.getUTCMinutes();
    const brtH = (utcH - 3 + 24) % 24;
    const brtMinutes = brtH * 60 + utcM;
    const day = now.getUTCDay();
    const isWeekday = day >= 1 && day <= 5;
    const isOpen = isWeekday && brtMinutes >= 600 && brtMinutes < 1075; // 10:00-17:55
    const isPre  = isWeekday && brtMinutes >= 570 && brtMinutes < 600;

    if (statusDot && statusTxt) {
      statusDot.className = 'status-dot ' + (isOpen ? 'open' : isPre ? 'pre' : 'closed');
      statusTxt.textContent = isOpen ? 'B3 ABERTO' : isPre ? 'PRE-ABERTURA' : 'B3 FECHADO';
      statusTxt.className = isOpen ? 'text-gain fs-11 fw-600' : isPre ? 'text-warning fs-11 fw-600' : 'text-muted fs-11';
    }
  }
  tick();
  setInterval(tick, 1000);
}

// ── Ticker Tape ──────────────────────────────────────────────────────────────
async function loadTickerTape() {
  const container = document.getElementById('ticker-content');
  if (!container) return;

  try {
    const res = await fetch('/api/exchanges/ticker-tape');
    if (!res.ok) throw new Error('ticker-tape error');
    const items = await res.json();

    if (!items || items.length === 0) return;

    // Duplicate for seamless loop
    const buildItem = (item) => {
      const cls = item.change >= 0 ? 'pos' : 'neg';
      return `<span class="ticker-item">
        <span class="t-symbol">${item.symbol}</span>
        <span class="t-price">${item.price}</span>
        <span class="t-change ${cls}">${changeArrow(item.change)} ${Math.abs(item.change).toFixed(2)}%</span>
      </span>`;
    };

    const html = items.map(buildItem).join('') + items.map(buildItem).join('');
    container.innerHTML = html;

    // Adjust animation duration based on item count
    const duration = Math.max(40, items.length * 4);
    container.style.animation = `ticker-scroll ${duration}s linear infinite`;

  } catch (e) {
    console.warn('[ticker] Could not load tape data:', e.message);
  }
}

// ── Tabs ─────────────────────────────────────────────────────────────────────
window._tabLoaded = {};

function showTab(name, btn) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

  const tab = document.getElementById('tab-' + name);
  if (tab) tab.classList.add('active');
  if (btn) btn.classList.add('active');

  if (!window._tabLoaded[name]) {
    window._tabLoaded[name] = true;
    if (name === 'portfolio') loadPortfolio();
    if (name === 'acoes')     loadAcoes();
    if (name === 'cryptos')   loadCryptos();
    if (name === 'watchlist') loadWatchlist();
  }
}

// ── Portfolio ────────────────────────────────────────────────────────────────
let portfolioChart = null;

async function loadPortfolio() {
  try {
    const res = await fetch('/api/portfolio/');
    const data = await res.json();
    const total = data.total || 395909;
    const items = data.items || [];

    // Update stat cards
    const statTotal = document.getElementById('stat-total');
    const statHoje  = document.getElementById('stat-hoje');
    const statHojePct = document.getElementById('stat-hoje-pct');
    const statRentab = document.getElementById('stat-rentab');

    if (statTotal) statTotal.textContent = fmtBRL(total);
    if (statHoje)  statHoje.textContent  = '+R$ 1.247,00';
    if (statHojePct) statHojePct.innerHTML = priceChangeSpan(0.32);
    if (statRentab) {
      statRentab.textContent = '+11,2% CDI';
      statRentab.className = 'stat-value cyan tabular';
    }

    // Table
    const wrap = document.getElementById('portfolio-table-wrap');
    if (wrap) {
      if (items.length === 0) {
        wrap.innerHTML = '<div class="empty-state">Nenhum item no portfolio.</div>';
      } else {
        let html = `<table class="data-table">
          <thead><tr>
            <th>PRODUTO</th>
            <th>TIPO</th>
            <th>INSTITUICAO</th>
            <th class="right">VALOR</th>
            <th>RENTABILIDADE</th>
          </tr></thead>
          <tbody>`;
        items.forEach(item => {
          const val = parseFloat(item.valor_atual || 0);
          const tipo = (item.tipo || '').toLowerCase();
          html += `<tr onclick="void(0)">
            <td><div class="ticker-cell">
              <span class="tk-symbol">${item.produto}</span>
            </div></td>
            <td><span class="badge-tipo ${tipo}">${item.tipo}</span></td>
            <td class="text-secondary">${item.instituicao || '—'}</td>
            <td class="right tabular fw-600">${fmtBRL(val)}</td>
            <td class="text-secondary fs-11">${item.rentabilidade_tipo || '—'}${item.taxa_anual ? ' ' + item.taxa_anual + '%' : ''}</td>
          </tr>`;
        });
        html += '</tbody></table>';
        wrap.innerHTML = html;
      }
    }

    // Chart
    renderPortfolioChart(items);

    // Sidebar markets
    loadSidebarMarkets();

  } catch (e) {
    console.error('[portfolio]', e);
    const w = document.getElementById('portfolio-table-wrap');
    if (w) w.innerHTML = '<div class="error-state">Erro ao carregar portfolio.</div>';
  }
}

function renderPortfolioChart(items) {
  const canvas = document.getElementById('portfolioChart');
  if (!canvas) return;
  if (portfolioChart) { portfolioChart.destroy(); portfolioChart = null; }

  const grupos = {};
  items.forEach(item => {
    const t = item.tipo || 'Outro';
    grupos[t] = (grupos[t] || 0) + parseFloat(item.valor_atual || 0);
  });

  // Defaults if no data
  const labels = Object.keys(grupos).length ? Object.keys(grupos) : ['Renda Fixa','VGBL','FIIs','Acoes','Crypto'];
  const values = Object.values(grupos).length ? Object.values(grupos) : [190000,160000,31000,15000,2000];
  const colors = ['#5b9cf6','#a78bfa','#00c853','#f59e0b','#f472b6'];

  portfolioChart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderColor: '#141b2d',
        borderWidth: 3,
        hoverBorderWidth: 1,
      }]
    },
    options: {
      responsive: true,
      cutout: '68%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#8b9dc3', font: { size: 11 }, padding: 12, usePointStyle: true },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${fmtBRL(ctx.parsed)}`,
          }
        }
      }
    }
  });
}

// ── Action Cards ─────────────────────────────────────────────────────────────
async function loadActionCards() {
  const row = document.getElementById('action-cards-row');
  const countBadge = document.getElementById('mentor-count');
  const sidebarMentor = document.getElementById('sidebar-mentor-cards');
  if (!row) return;

  try {
    const res = await fetch('/api/sugestoes/cards');
    const cards = await res.json();

    if (!cards || cards.length === 0) {
      row.innerHTML = '<div class="empty-state fs-12 text-muted">Nenhuma sugestao ativa no momento.</div>';
      if (countBadge) countBadge.textContent = '0 ativos';
      return;
    }

    if (countBadge) countBadge.textContent = `${cards.length} ativo${cards.length > 1 ? 's' : ''}`;

    const typeMap = { oportunidade: 'oportunidade', alerta: 'alerta', rebalanceamento: 'rebalanceamento', noticia: 'noticia' };

    row.innerHTML = cards.map(card => {
      const typeCls = typeMap[card.tipo] || 'noticia';
      const gainHtml = card.ganho_potencial
        ? `<div class="action-card-metric"><span class="metric-label">Potencial</span><span class="metric-value green">+${card.ganho_potencial}%</span></div>` : '';
      const btns = (card.acoes_sugeridas || []).map(a =>
        `<button class="btn-action primary" onclick="executarAcaoCard('${a.acao}','${card.ticker||''}',${card.id})">${a.label}</button>`
      ).join('');
      return `<div class="action-card" data-card-id="${card.id}">
        <div class="action-card-header">
          <span class="action-card-type ${typeCls}">${card.tipo.toUpperCase()}</span>
          ${card.ticker ? `<span class="action-card-ticker">${card.ticker}</span>` : ''}
        </div>
        <div class="action-card-title">${card.titulo}</div>
        <div class="action-card-desc">${card.descricao}</div>
        ${gainHtml}
        <div class="action-card-buttons">
          ${btns}
          <button class="btn-action dismiss" onclick="descartarCard(${card.id})" title="Descartar">✕</button>
        </div>
      </div>`;
    }).join('');

    // Sidebar mini cards (last 2)
    if (sidebarMentor) {
      sidebarMentor.innerHTML = cards.slice(0, 2).map(card => {
        const typeCls = typeMap[card.tipo] || 'noticia';
        return `<div class="sidebar-card-mini">
          <div class="scm-type ${typeCls}">${card.tipo.toUpperCase()}</div>
          <div class="scm-title">${card.titulo}</div>
          ${card.ticker ? `<div class="scm-sub">${card.ticker}</div>` : ''}
        </div>`;
      }).join('');
    }

  } catch (e) {
    console.error('[action-cards]', e);
    if (row) row.innerHTML = '<div class="empty-state text-muted fs-12">Nenhuma sugestao disponivel.</div>';
  }
}

function executarAcaoCard(acao, ticker, cardId) {
  switch (acao) {
    case 'ver_ativo': case 'ver_grafico':
      if (ticker) abrirModalHistorico(ticker); break;
    case 'ver_noticias':
      window.location.href = '/noticias.html'; break;
    case 'watchlist': case 'ver_oportunidades':
      showTab('watchlist', document.querySelector('[onclick*="watchlist"]')); break;
    case 'cenarios': case 'simular': case 'rebalancear':
      window.location.href = '/cenarios.html'; break;
    default: break;
  }
  fetch(`/api/sugestoes/executar-card/${cardId}`, { method: 'POST' }).catch(() => {});
}

function descartarCard(cardId) {
  fetch(`/api/sugestoes/descartar-card/${cardId}`, { method: 'POST' })
    .then(() => {
      const el = document.querySelector(`[data-card-id="${cardId}"]`);
      if (el) { el.style.opacity = '0'; el.style.transform = 'scale(0.9)'; el.style.transition = 'all 0.2s'; setTimeout(() => el.remove(), 200); }
    }).catch(() => {});
}

// ── Acoes B3 ─────────────────────────────────────────────────────────────────
async function loadAcoes() {
  const wrap = document.getElementById('acoes-table-wrap');
  const upd  = document.getElementById('acoes-last-update');
  if (!wrap) return;
  wrap.innerHTML = '<div class="loading-state"><div class="loading-spinner"></div> Carregando acoes...</div>';

  try {
    const res = await fetch('/api/exchanges/acoes-b3');
    const data = await res.json();
    if (upd) upd.textContent = 'Atualizado ' + new Date().toLocaleTimeString('pt-BR');

    if (!data || data.length === 0) {
      wrap.innerHTML = '<div class="empty-state">Sem dados de acoes.</div>';
      return;
    }

    let html = `<table class="data-table">
      <thead><tr>
        <th>TICKER</th>
        <th class="right">PRECO</th>
        <th class="right">VARIACAO</th>
        <th>STATUS</th>
      </tr></thead>
      <tbody>`;

    data.forEach(a => {
      const chgCls = changeClass(a.change_pct);
      html += `<tr onclick="abrirModalHistorico('${a.ticker}')">
        <td><div class="ticker-cell">
          <span class="tk-symbol">${a.ticker}</span>
          <span class="tk-name">${a.name}</span>
        </div></td>
        <td class="right tabular fw-600">R$ ${a.price.toFixed(2)}</td>
        <td class="right">${priceBadge(a.change_pct)}</td>
        <td>${a.source === 'static' ? '<span class="text-muted fs-11">estimado</span>' : '<span class="text-gain fs-11">ao vivo</span>'}</td>
      </tr>`;
    });

    html += '</tbody></table>';
    wrap.innerHTML = html;

  } catch (e) {
    console.error('[acoes]', e);
    wrap.innerHTML = '<div class="error-state">Erro ao carregar acoes B3.</div>';
  }
}

// ── Cryptos ───────────────────────────────────────────────────────────────────
async function loadCryptos() {
  const wrap = document.getElementById('cryptos-grid-wrap');
  const upd  = document.getElementById('cryptos-last-update');
  if (!wrap) return;
  wrap.innerHTML = '<div class="loading-state"><div class="loading-spinner"></div> Carregando cryptos...</div>';

  try {
    const res = await fetch('/api/exchanges/cryptos');
    const data = await res.json();
    if (upd) upd.textContent = 'Atualizado ' + new Date().toLocaleTimeString('pt-BR');

    if (!data || data.length === 0) {
      wrap.innerHTML = '<div class="empty-state">Sem dados de cryptos.</div>';
      return;
    }

    const gridHtml = `<div class="crypto-grid">` + data.map(c => {
      const p = c.price_brl;
      const fmtP = p >= 1000 ? fmtBRL(p, 0) : p >= 1 ? fmtBRL(p, 2) : `R$ ${p.toFixed(6)}`;
      const chgCls = changeClass(c.change_24h);
      return `<div class="crypto-card">
        <div class="cc-symbol">${c.symbol}</div>
        <div class="cc-name">${c.name}</div>
        <div class="cc-price">${fmtP}</div>
        <div class="cc-change price-change ${chgCls}">${changeArrow(c.change_24h)} ${Math.abs(c.change_24h).toFixed(2)}%</div>
      </div>`;
    }).join('') + `</div>`;

    // Also show a table below
    let tableHtml = `<div class="mt-16"><table class="data-table">
      <thead><tr>
        <th>SYMBOL</th>
        <th class="right">PRECO (BRL)</th>
        <th class="right">PRECO (USD)</th>
        <th class="right">24H</th>
      </tr></thead>
      <tbody>`;

    data.forEach(c => {
      const p = c.price_brl;
      const fmtP = p >= 1000 ? fmtBRL(p, 0) : p >= 1 ? fmtBRL(p, 2) : `R$ ${p.toFixed(6)}`;
      const fmtU = `$ ${c.price_usd >= 1 ? c.price_usd.toFixed(2) : c.price_usd.toFixed(6)}`;
      tableHtml += `<tr>
        <td><div class="ticker-cell">
          <span class="tk-symbol">${c.symbol}</span>
          <span class="tk-name">${c.name}</span>
        </div></td>
        <td class="right tabular fw-600">${fmtP}</td>
        <td class="right tabular text-secondary">${fmtU}</td>
        <td class="right">${priceBadge(c.change_24h)}</td>
      </tr>`;
    });

    tableHtml += '</tbody></table></div>';
    wrap.innerHTML = gridHtml + tableHtml;

  } catch (e) {
    console.error('[cryptos]', e);
    wrap.innerHTML = '<div class="error-state">Erro ao carregar criptomoedas.</div>';
  }
}

// ── Watchlist ─────────────────────────────────────────────────────────────────
async function loadWatchlist() {
  const wrap = document.getElementById('watchlist-table-wrap');
  if (!wrap) return;
  wrap.innerHTML = '<div class="loading-state"><div class="loading-spinner"></div> Carregando watchlist...</div>';

  try {
    const res = await fetch('/api/portfolio/watchlist');
    const data = await res.json();

    if (!data || data.length === 0) {
      wrap.innerHTML = '<div class="empty-state">Watchlist vazia.</div>';
      return;
    }

    const semMap = { 'verde': 'verde', 'amarelo-verde': 'amarelo', 'amarelo': 'amarelo', 'vermelho': 'vermelho' };
    const veredictoColors = { 'Favoravel': 'var(--gain)', 'Aceitavel': '#5b9cf6', 'Neutro': 'var(--neutral)', 'Desfavoravel': 'var(--loss)' };

    let html = `<table class="data-table">
      <thead><tr>
        <th></th>
        <th>TICKER</th>
        <th class="right">ENTRADA</th>
        <th class="right">ATUAL</th>
        <th class="right">ALVO</th>
        <th class="right">STOP</th>
        <th>PROGRESSO</th>
        <th>VEREDICTO</th>
      </tr></thead>
      <tbody>`;

    data.forEach(item => {
      const precoAtual = item.preco_atual || item.entrada;
      const semDot = semMap[item.semaforo] || 'amarelo';
      const variacaoDia = item.variacao_dia || 0;
      const veredicto = item.veredicto || 'Neutro';
      const verColor = veredictoColors[veredicto] || 'var(--neutral)';
      const progresso = item.progresso || 0;

      html += `<tr onclick="abrirModalHistorico('${item.ticker}')" title="Clique para ver historico">
        <td class="center"><span class="semaphore-dot ${semDot}"></span></td>
        <td><div class="ticker-cell">
          <span class="tk-symbol">${item.ticker}</span>
          <span class="tk-name">${item.nome || ''}</span>
        </div></td>
        <td class="right tabular">R$ ${item.entrada ? item.entrada.toFixed(2) : '—'}</td>
        <td class="right tabular">
          R$ ${precoAtual ? precoAtual.toFixed(2) : '—'}
          ${priceChangeSpan(variacaoDia)}
        </td>
        <td class="right tabular text-gain">R$ ${item.alvo ? item.alvo.toFixed(2) : '—'}</td>
        <td class="right tabular text-loss">R$ ${item.stop ? item.stop.toFixed(2) : '—'}</td>
        <td style="min-width:100px;">
          <div class="progress-bar">
            <div class="progress-fill" style="width:${Math.min(100,Math.max(0,progresso))}%"></div>
          </div>
          <div class="fs-11 text-muted mt-4">${progresso.toFixed(1)}%</div>
        </td>
        <td><span style="color:${verColor};font-weight:700;font-size:12px;">${veredicto}</span></td>
      </tr>`;
    });

    html += '</tbody></table>';
    wrap.innerHTML = html;

  } catch (e) {
    console.error('[watchlist]', e);
    wrap.innerHTML = '<div class="error-state">Erro ao carregar watchlist.</div>';
  }
}

// ── Sidebar Markets ───────────────────────────────────────────────────────────
async function loadSidebarMarkets() {
  const el = document.getElementById('sidebar-markets');
  if (!el) return;

  try {
    const [moedas, cryptos] = await Promise.all([
      fetch('/api/exchanges/moedas-expandido').then(r => r.json()),
      fetch('/api/exchanges/cryptos').then(r => r.json()),
    ]);

    const items = [];

    // IBOV placeholder
    items.push({ name: 'IBOV', value: '127.843', change: 0.54 });

    if (Array.isArray(moedas)) {
      const usd = moedas.find(m => m.symbol === 'USD');
      if (usd) items.push({ name: 'USD/BRL', value: `R$ ${usd.price.toFixed(2)}`, change: usd.change_pct });
    }

    if (Array.isArray(cryptos)) {
      const btc = cryptos.find(c => c.symbol === 'BTC');
      if (btc) items.push({ name: 'BTC', value: fmtBRLCompact(btc.price_brl), change: btc.change_24h });
      const eth = cryptos.find(c => c.symbol === 'ETH');
      if (eth) items.push({ name: 'ETH', value: fmtBRLCompact(eth.price_brl), change: eth.change_24h });
    }

    el.innerHTML = items.map(item => {
      const cls = item.change >= 0 ? 'text-gain' : 'text-loss';
      return `<div class="sidebar-market-item">
        <span class="sm-name">${item.name}</span>
        <div style="text-align:right;">
          <div class="sm-value">${item.value}</div>
          <div class="sm-change ${cls}">${changeArrow(item.change)} ${Math.abs(item.change).toFixed(2)}%</div>
        </div>
      </div>`;
    }).join('');
  } catch (e) {
    el.innerHTML = '<div class="text-muted fs-11" style="padding:4px 6px;">Sem dados</div>';
  }
}

// ── Modals ────────────────────────────────────────────────────────────────────
window.currentTicker = null;
window.historicoChart = null;

function abrirModalHistorico(ticker) {
  window.currentTicker = ticker;
  const modal = document.getElementById('modal-historico');
  const title = document.getElementById('historico-titulo');
  if (!modal) return;
  modal.classList.add('open');
  if (title) title.textContent = `${ticker} — Historico de Preco`;
  carregarHistorico(ticker, '1y', modal.querySelector('.period-btn.active'));
}

function fecharModalHistorico() {
  const modal = document.getElementById('modal-historico');
  if (modal) modal.classList.remove('open');
  if (window.historicoChart) { window.historicoChart.destroy(); window.historicoChart = null; }
}

async function carregarHistorico(ticker, periodo, btn) {
  if (!ticker) return;
  if (btn) {
    document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  }

  const statsEl = document.getElementById('historico-stats');
  const canvas  = document.getElementById('historicoChart');
  if (!statsEl || !canvas) return;
  statsEl.innerHTML = '<div class="loading-state" style="padding:12px;"><div class="loading-spinner"></div> Carregando...</div>';

  try {
    const res  = await fetch(`/api/historico/${ticker}?periodo=${periodo}`);
    const data = await res.json();

    if (!data.data || data.data.length === 0) {
      statsEl.innerHTML = '<div class="text-muted fs-12">Sem dados para este periodo.</div>';
      return;
    }

    const prices = data.data.map(d => d.close);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const variacao = ((prices[prices.length-1] - prices[0]) / prices[0] * 100).toFixed(2);
    const info = TICKER_INFO[ticker] || {};

    statsEl.innerHTML = `<div class="flex gap-12 mb-12 flex-wrap">
      <div><span class="text-muted fs-11">Minimo</span><br><span class="fw-600">R$ ${min.toFixed(2)}</span></div>
      <div><span class="text-muted fs-11">Maximo</span><br><span class="fw-600">R$ ${max.toFixed(2)}</span></div>
      <div><span class="text-muted fs-11">Variacao</span><br>${priceChangeSpan(parseFloat(variacao))}</div>
      ${info.entrada ? `<div><span class="text-muted fs-11">Entrada</span><br><span class="fw-600 text-warning">R$ ${info.entrada.toFixed(2)}</span></div>` : ''}
      ${info.alvo   ? `<div><span class="text-muted fs-11">Alvo</span><br><span class="fw-600 text-gain">R$ ${info.alvo.toFixed(2)}</span></div>` : ''}
      ${info.stop   ? `<div><span class="text-muted fs-11">Stop</span><br><span class="fw-600 text-loss">R$ ${info.stop.toFixed(2)}</span></div>` : ''}
    </div>`;

    if (window.historicoChart) { window.historicoChart.destroy(); window.historicoChart = null; }

    const ctx = canvas.getContext('2d');
    window.historicoChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.data.map(d => d.date),
        datasets: [{
          label: ticker,
          data: prices,
          borderColor: '#00d4ff',
          backgroundColor: 'rgba(0,212,255,0.06)',
          fill: true,
          tension: 0.2,
          pointRadius: 0,
          borderWidth: 1.5,
        }]
      },
      options: {
        responsive: true,
        animation: { duration: 300 },
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ` R$ ${ctx.parsed.y.toFixed(2)}`
            }
          }
        },
        scales: {
          y: {
            ticks: { color: '#8b9dc3', font: { size: 11 } },
            grid:  { color: 'rgba(255,255,255,0.04)' },
          },
          x: {
            ticks: { color: '#8b9dc3', font: { size: 10 }, maxTicksLimit: 8 },
            grid:  { display: false },
          }
        }
      }
    });
  } catch (e) {
    statsEl.innerHTML = '<div class="error-state">Erro ao carregar historico.</div>';
  }
}

// Close modal on backdrop click
document.addEventListener('click', (e) => {
  const modal = document.getElementById('modal-historico');
  if (modal && e.target === modal) fecharModalHistorico();
});

// ── Logout ────────────────────────────────────────────────────────────────────
function fazerLogout() {
  fetch('/api/auth/logout', { method: 'POST' }).finally(() => {
    document.cookie = 'token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    window.location.href = '/login.html';
  });
}

// ── Auto-refresh ──────────────────────────────────────────────────────────────
let refreshInterval = null;

function startAutoRefresh() {
  if (refreshInterval) clearInterval(refreshInterval);
  refreshInterval = setInterval(async () => {
    await loadTickerTape();
    await loadSidebarMarkets();

    // Refresh active tab data
    const activeTabs = document.querySelectorAll('.tab-content.active');
    activeTabs.forEach(tab => {
      const name = tab.id.replace('tab-', '');
      if (name === 'portfolio') loadPortfolio();
      if (name === 'acoes')     { loadAcoes(); }
      if (name === 'cryptos')   { loadCryptos(); }
    });
  }, 30000); // 30 seconds
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  startClock();

  // Initial loads
  await loadTickerTape();
  loadPortfolio();
  loadActionCards();
  startAutoRefresh();
});
