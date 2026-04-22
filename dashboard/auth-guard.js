// InvestAI Auth Guard - SIMPLIFICADO

(function() {
    'use strict';

    async function verificarAutenticacao() {
        try {
            const res = await fetch('/api/auth/me', {
                credentials: 'include'
            });

            if (res.ok) {
                const data = await res.json();
                if (data.username) {
                    // Autenticado
                    const usernameDisplay = document.getElementById('username-display');
                    if (usernameDisplay) {
                        usernameDisplay.textContent = `👤 ${data.username}`;
                    }
                    return; // OK
                }
            }
            
            // Não autenticado - redireciona
            window.location.replace('/login.html');
            
        } catch (e) {
            window.location.replace('/login.html');
        }
    }

    // Executa apenas se não estiver na página de login
    const path = window.location.pathname;
    if (!path.includes('login.html') && !path.includes('test-auth.html')) {
        verificarAutenticacao();
    }
})();
