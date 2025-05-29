const CACHE_NAME = 'pistonews-cache-v1';
const urlsToCache = [
  '/',  // pagina iniziale
  '/static/style.css',  // CSS
  '/static/updloads/Logo.png',   // logo o immagine se esiste
  // aggiungi altri file statici qui
];

// Durante l'installazione, cache i file specificati
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

// Risponde alle richieste con contenuto dalla cache se disponibile
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});

// Rimuove la cache vecchia quando aggiorni il service worker
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames =>
      Promise.all(
        cacheNames.map(cacheName => {
          if (!cacheWhitelist.includes(cacheName)) {
            return caches.delete(cacheName);
          }
        })
      )
    )
  );
});
