/* ================================================
   SW.JS — Service Worker PWA avec cache intelligent
   Stratégies : Cache-First (statiques), Network-First (dynamique)
   ================================================ */

const CACHE_STATIQUE = 'bta-static-v2';
const CACHE_DYNAMIQUE = 'bta-dynamic-v2';
const CACHE_LECONS = 'bta-lecons-offline-v1';

const RESSOURCES_STATIQUES = [
    '/static/academie/style.css',
    '/static/academie/icons/icon-192.png',
    '/static/academie/icons/icon-512.png',
];

// ---- INSTALLATION : met en cache les ressources statiques ----
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_STATIQUE).then(function(cache) {
            return cache.addAll(RESSOURCES_STATIQUES);
        })
    );
    self.skipWaiting();
});

// ---- ACTIVATION : nettoie les vieux caches ----
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(noms) {
            return Promise.all(
                noms.filter(nom => ![CACHE_STATIQUE, CACHE_DYNAMIQUE, CACHE_LECONS].includes(nom))
                    .map(nom => caches.delete(nom))
            );
        })
    );
    self.clients.claim();
});

// ---- FETCH : stratégie selon le type de requête ----
self.addEventListener('fetch', function(event) {
    const url = new URL(event.request.url);

    // Ressources statiques → Cache First
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(event.request).then(reponse => reponse || fetch(event.request))
        );
        return;
    }

    // Leçons téléchargées → priorité cache offline
    if (url.pathname.includes('/lecon/')) {
        event.respondWith(
            caches.open(CACHE_LECONS).then(function(cache) {
                return cache.match(event.request).then(function(reponseCache) {
                    const fetchPromise = fetch(event.request).then(function(reponseReseau) {
                        cache.put(event.request, reponseReseau.clone());
                        return reponseReseau;
                    }).catch(() => reponseCache);
                    return reponseCache || fetchPromise;
                });
            })
        );
        return;
    }

    // Pages dynamiques → Network First avec fallback cache
    event.respondWith(
        fetch(event.request)
            .then(function(reponse) {
                const reponseClone = reponse.clone();
                caches.open(CACHE_DYNAMIQUE).then(cache => cache.put(event.request, reponseClone));
                return reponse;
            })
            .catch(function() {
                return caches.match(event.request).then(function(reponseCache) {
                    return reponseCache || caches.match('/offline/');
                });
            })
    );
});

// ---- SYNC EN ARRIÈRE-PLAN : synchronise au retour internet ----
self.addEventListener('sync', function(event) {
    if (event.tag === 'sync-progression') {
        event.waitUntil(synchroniserProgressionEnAttente());
    }
});

async function synchroniserProgressionEnAttente() {
    // Récupère les progressions stockées localement pendant l'offline
    const db = await ouvrirBaseIndexedDB();
    const transaction = db.transaction('progressions_attente', 'readonly');
    const store = transaction.objectStore('progressions_attente');
    const toutes = await new Promise(resolve => {
        const req = store.getAll();
        req.onsuccess = () => resolve(req.result);
    });

    for (const item of toutes) {
        try {
            await fetch(`/lecon/${item.lecon_id}/terminer/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': item.csrf_token },
            });
        } catch (e) { /* réessaiera au prochain sync */ }
    }
}

function ouvrirBaseIndexedDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('bta-offline-db', 1);
        request.onupgradeneeded = function(e) {
            const db = e.target.result;
            if (!db.objectStoreNames.contains('lecons_telechargees')) {
                db.createObjectStore('lecons_telechargees', { keyPath: 'lecon_id' });
            }
            if (!db.objectStoreNames.contains('progressions_attente')) {
                db.createObjectStore('progressions_attente', { keyPath: 'lecon_id' });
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = reject;
    });
}