// InvestAI Chat Widget - IA Contextual Proativa

(function() {
    'use strict';

    // CONTEXTO POR PÁGINA
    const PAGE_CONTEXTS = {
        '/': {
            nome: 'Dashboard Principal',
            contexto: 'Você está vendo o painel principal com seu portfolio completo, ações, cryptos e watchlist.',
            sugestoes: [
                '💰 Qual meu total investido?',
                '📊 Qual ativo teve melhor desempenho?',
                '🎯 Devo rebalancear minha carteira?'
            ]
        },
        '/index.html': {
            nome: 'Dashboard Principal',
            contexto: 'Você está vendo o painel principal com seu portfolio completo.',
            sugestoes: [
                '💰 Quanto tenho investido?',
                '📈 Como está meu portfolio hoje?',
                '🔍 Mostrar resumo dos investimentos'
            ]
        },
        '/cenarios.html': {
            nome: 'Cenários de Investimento',
            contexto: 'Você está analisando 4 cenários de rebalanceamento: Atual, Conservador, Moderado e Arrojado.',
            sugestoes: [
                '💡 Qual cenário é melhor para mim?',
                '📊 Compare conservador vs arrojado',
                '🧮 Simule SELIC a 10%'
            ]
        },
        '/plano.html': {
            nome: 'Plano de Ação',
            contexto: 'Você está no guia passo a passo para executar seu cenário escolhido.',
            sugestoes: [
                '✅ Por onde começar?',
                '🏦 Como investir no Tesouro?',
                '📋 Mostre o checklist completo'
            ]
        },
        '/noticias.html': {
            nome: 'Radar de Mercado',
            contexto: 'Você está vendo mercados globais em tempo real, notícias e análise de IA.',
            sugestoes: [
                '📰 Resuma as principais notícias',
                '📊 Como está o mercado hoje?',
                '🌍 Qual o cenário global?'
            ]
        },
        '/smartmoney.html': {
            nome: 'Smart Money',
            contexto: 'Você está analisando movimentos institucionais, volume anômalo e insider trading.',
            sugestoes: [
                '👀 Detectou algo suspeito?',
                '📈 Quais ações têm volume alto?',
                '🔔 Há algum alerta importante?'
            ]
        },
        '/mobile.html': {
            nome: 'Mobile',
            contexto: 'Você está na versão mobile do InvestAI.',
            sugestoes: [
                '💰 Resumo rápido',
                '📊 Como está hoje?',
                '🎯 Próxima ação?'
            ]
        }
    };

    // ESTADO
    let chatAberto = false;
    let mensagens = [];
    let aguardandoResposta = false;

    // MEMÓRIA
    function salvarMemoriaSessao() {
        const ultimas40 = mensagens.slice(-40);
        sessionStorage.setItem('investai_chat_sessao', JSON.stringify(ultimas40));
    }

    function carregarMemoriaSessao() {
        const saved = sessionStorage.getItem('investai_chat_sessao');
        if (saved) {
            mensagens = JSON.parse(saved);
        }
    }

    function salvarMemoriaLongo(resumo) {
        let historico = JSON.parse(localStorage.getItem('investai_chat_historico') || '[]');
        historico.push({
            data: new Date().toISOString(),
            resumo: resumo
        });
        historico = historico.slice(-20); // Mantém últimos 20
        localStorage.setItem('investai_chat_historico', JSON.stringify(historico));
    }

    // UI
    function criarWidget() {
        const html = `
            <div id="investai-chat-widget">
                <button id="investai-chat-btn" class="chat-btn">🤖</button>
                <div id="investai-chat-container" class="chat-container">
                    <div class="chat-header">
                        <div class="chat-header-info">
                            <span class="chat-title">💬 InvestAI Assistant</span>
                            <span class="chat-subtitle" id="chat-page-name"></span>
                        </div>
                        <div class="chat-header-actions">
                            <button id="chat-insight-btn" class="btn-insight" title="Gerar Insight">✨</button>
                            <button id="chat-close-btn" class="btn-close">✕</button>
                        </div>
                    </div>
                    <div class="chat-sugestoes" id="chat-sugestoes"></div>
                    <div class="chat-messages" id="chat-messages"></div>
                    <div class="chat-input-container">
                        <textarea id="chat-input" placeholder="Digite sua mensagem..."></textarea>
                        <button id="chat-send-btn">Enviar</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', html);

        // Estilos
        const styles = `
            #investai-chat-widget {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 9999;
            }
            .chat-btn {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                font-size: 28px;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                transition: transform 0.2s;
            }
            .chat-btn:hover {
                transform: scale(1.1);
            }
            .chat-container {
                display: none;
                flex-direction: column;
                position: fixed;
                bottom: 90px;
                right: 20px;
                width: 400px;
                height: 600px;
                background: #1a1a2e;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.4);
                border: 1px solid rgba(0, 212, 255, 0.3);
            }
            .chat-container.aberto {
                display: flex;
                animation: slideIn 0.3s ease-out;
            }
            @keyframes slideIn {
                from { transform: translateY(20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            .chat-header {
                padding: 15px;
                background: rgba(0, 212, 255, 0.1);
                border-bottom: 1px solid rgba(0, 212, 255, 0.2);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .chat-header-info {
                display: flex;
                flex-direction: column;
            }
            .chat-title {
                font-weight: bold;
                color: #00d4ff;
            }
            .chat-subtitle {
                font-size: 0.85em;
                color: #94a3b8;
            }
            .chat-header-actions {
                display: flex;
                gap: 10px;
            }
            .btn-insight, .btn-close {
                background: transparent;
                border: none;
                color: #00d4ff;
                cursor: pointer;
                font-size: 18px;
            }
            .chat-sugestoes {
                padding: 10px;
                display: flex;
                flex-direction: column;
                gap: 5px;
                border-bottom: 1px solid rgba(0, 212, 255, 0.1);
            }
            .sugestao-btn {
                padding: 8px 12px;
                background: rgba(0, 212, 255, 0.1);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
                color: #e0e0e0;
                cursor: pointer;
                text-align: left;
                font-size: 0.9em;
                transition: background 0.2s;
            }
            .sugestao-btn:hover {
                background: rgba(0, 212, 255, 0.2);
            }
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .chat-message {
                padding: 10px 15px;
                border-radius: 12px;
                max-width: 85%;
                word-wrap: break-word;
            }
            .chat-message.user {
                background: #00d4ff;
                color: #1a1a2e;
                align-self: flex-end;
            }
            .chat-message.assistant {
                background: rgba(255, 255, 255, 0.05);
                color: #e0e0e0;
                align-self: flex-start;
                border: 1px solid rgba(0, 212, 255, 0.2);
            }
            .chat-input-container {
                padding: 15px;
                display: flex;
                gap: 10px;
                border-top: 1px solid rgba(0, 212, 255, 0.2);
            }
            #chat-input {
                flex: 1;
                padding: 10px;
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
                color: #e0e0e0;
                resize: none;
                font-family: inherit;
            }
            #chat-send-btn {
                padding: 10px 20px;
                background: #00d4ff;
                border: none;
                border-radius: 8px;
                color: #1a1a2e;
                font-weight: bold;
                cursor: pointer;
            }
            #chat-send-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            .chat-toast {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #1a1a2e;
                border: 2px solid #00d4ff;
                border-radius: 12px;
                padding: 15px 20px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 10000;
                animation: toastIn 0.3s ease-out;
            }
            @keyframes toastIn {
                from { transform: translateX(400px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            .badge-urgencia {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.8em;
                font-weight: bold;
            }
            .badge-urgencia.alta { background: #ef4444; color: white; }
            .badge-urgencia.media { background: #f59e0b; color: white; }
            .badge-urgencia.baixa { background: #10b981; color: white; }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    function atualizarContextoPagina() {
        const path = window.location.pathname;
        const contexto = PAGE_CONTEXTS[path] || PAGE_CONTEXTS['/'];
        
        document.getElementById('chat-page-name').textContent = contexto.nome;
        
        const sugestoesHTML = contexto.sugestoes.map(s => 
            `<button class="sugestao-btn" onclick="window.enviarSugestao('${s}')">${s}</button>`
        ).join('');
        
        document.getElementById('chat-sugestoes').innerHTML = sugestoesHTML;
    }

    function adicionarMensagem(texto, tipo) {
        mensagens.push({ texto, tipo, timestamp: new Date().toISOString() });
        
        const messagesDiv = document.getElementById('chat-messages');
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${tipo}`;
        msgDiv.textContent = texto;
        messagesDiv.appendChild(msgDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;

        salvarMemoriaSessao();
    }

    async function enviarMensagem(mensagem) {
        if (!mensagem || aguardandoResposta) return;

        adicionarMensagem(mensagem, 'user');
        aguardandoResposta = true;
        document.getElementById('chat-send-btn').disabled = true;

        try {
            const path = window.location.pathname;
            const contexto = PAGE_CONTEXTS[path] || PAGE_CONTEXTS['/'];
            
            const historico = mensagens.slice(-10).map(m => ({
                role: m.tipo === 'user' ? 'user' : 'assistant',
                content: m.texto
            }));

            const res = await fetch('/api/chat/context', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mensagem: mensagem,
                    pagina_atual: contexto.nome,
                    contexto_pagina: contexto.contexto,
                    historico_sessao: historico
                })
            });

            const data = await res.json();
            adicionarMensagem(data.resposta, 'assistant');
        } catch (e) {
            console.error('Erro no chat:', e);
            adicionarMensagem('Desculpe, ocorreu um erro. Tente novamente.', 'assistant');
        } finally {
            aguardandoResposta = false;
            document.getElementById('chat-send-btn').disabled = false;
        }
    }

    window.enviarSugestao = function(texto) {
        // Remove emoji do início se existir
        const limpo = texto.replace(/^[^\w\s]+\s/, '');
        document.getElementById('chat-input').value = limpo;
        enviarMensagem(limpo);
    };

    async function gerarInsightProativo() {
        try {
            const res = await fetch('/api/chat/proativo/gerar', { method: 'POST' });
            const data = await res.json();
            
            if (data.mensagem) {
                mostrarToast(data.mensagem, data.urgencia);
            }
        } catch (e) {
            console.error('Erro ao gerar insight:', e);
        }
    }

    function mostrarToast(mensagem, urgencia = 'media') {
        const toast = document.createElement('div');
        toast.className = 'chat-toast';
        toast.innerHTML = `
            <div><strong>🤖 Insight Proativo</strong> <span class="badge-urgencia ${urgencia}">${urgencia.toUpperCase()}</span></div>
            <p style="margin: 10px 0 0 0;">${mensagem}</p>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 8000);
    }

    async function verificarInsightsProativos() {
        try {
            const res = await fetch('/api/chat/proativo');
            const data = await res.json();
            
            if (data.mensagem) {
                mostrarToast(data.mensagem, data.urgencia);
                
                // Marca como lida
                await fetch('/api/chat/proativo/limpar', { method: 'POST' });
            }
        } catch (e) {
            // Silencioso - endpoint pode não ter mensagens pendentes
        }
    }

    // INICIALIZAÇÃO
    function init() {
        criarWidget();
        carregarMemoriaSessao();
        atualizarContextoPagina();

        // Event listeners
        document.getElementById('investai-chat-btn').addEventListener('click', () => {
            chatAberto = !chatAberto;
            const container = document.getElementById('investai-chat-container');
            if (chatAberto) {
                container.classList.add('aberto');
            } else {
                container.classList.remove('aberto');
            }
        });

        document.getElementById('chat-close-btn').addEventListener('click', () => {
            chatAberto = false;
            document.getElementById('investai-chat-container').classList.remove('aberto');
        });

        document.getElementById('chat-send-btn').addEventListener('click', () => {
            const input = document.getElementById('chat-input');
            enviarMensagem(input.value);
            input.value = '';
        });

        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                document.getElementById('chat-send-btn').click();
            }
        });

        document.getElementById('chat-insight-btn').addEventListener('click', () => {
            gerarInsightProativo();
        });

        // Polling proativo a cada 3 minutos
        setInterval(verificarInsightsProativos, 3 * 60 * 1000);
        
        // Verifica ao carregar
        setTimeout(verificarInsightsProativos, 5000);
    }

    // Aguarda DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
