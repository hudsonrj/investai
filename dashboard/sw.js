// InvestAI Service Worker v2

const CACHE_NAME = 'investai-v2';
const ASSETS = [
    '/',
    '/index.html',
    '/cenarios.html',
    '/plano.html',
    '/noticias.html',
    '/smartmoney.html',
    '/mobile.html',
    '/static/style.css',
    '/static/app-v2.js',
    '/dashboard/auth-guard.js',
    '/dashboard/chat-widget.js'
];

// Instala e cacheia
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Ativa e limpa caches antigos
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch: network-first com fallback para cache
self.addEventListener('fetch', (event) => {
    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Clona e cacheia resposta
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, responseClone);
                });
                return response;
            })
            .catch(() => {
                // Se falhar, tenta cache
                return caches.match(event.request);
            })
    );
});
