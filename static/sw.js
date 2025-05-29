const CACHE_NAME = 'pistonews-cache-v4';
const DYNAMIC_CACHE_NAME = 'pistonews-dynamic-cache-v1';

const urlsToCache = [
  '/',
  '/offline.html',
  '/static/style.css',             // <-- Cambia con il tuo file CSS reale
  '/static/manifest.json',
  '/static/icon-192.png',
  '/static/icon-512.png'
];

// Installa e cachea risorse statiche
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

// Attiva e rimuove vecchie cache
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME, DYNAMIC_CACHE_NAME];
  event.waitUntil(
    caches.keys().then(names =>
      Promise.all(
        names.map(name => {
          if (!cacheWhitelist.includes(name)) {
            return caches.delete(name);
          }
        })
      )
    )
  );
});

// Gestione delle richieste (fetch)
self.addEventListener('fetch', event => {
  const request = event.request;
  const requestUrl = new URL(request.url);

  // Navigazione (HTML dinamico)
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then(response => {
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          const responseClone = response.clone();
          caches.open(DYNAMIC_CACHE_NAME).then(cache => {
            cache.put(request, responseClone);
          });

          return response;
        })
        .catch(() => {
          return caches.match(request).then(cachedRes => cachedRes || caches.match('/templates/offline.html'));
        })
    );
    return;
  }

  // Cache dinamica per immagini caricate (upload)
  if (requestUrl.pathname.startsWith('/static/upload/')) {
    event.respondWith(
      caches.open(DYNAMIC_CACHE_NAME).then(cache =>
        fetch(request)
          .then(response => {
            if (response && response.status === 200) {
              cache.put(request, response.clone());
            }
            return response;
          })
          .catch(() => caches.match(request))
      )
    );
    return;
  }

  // Risorse statiche già note
  if (urlsToCache.includes(requestUrl.pathname)) {
    event.respondWith(
      caches.match(request).then(cachedRes => cachedRes || fetch(request))
    );
    return;
  }

  // Fallback generico: prima cache, poi offline.html
  event.respondWith(
    fetch(request)
      .catch(() =>
        caches.match(request).then(cachedRes => cachedRes || caches.match('/templates/offline.html'))
      )
  );
});
