// Installa e cache statici
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

// Attiva e pulisci cache vecchie
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

// Gestione fetch con cache dinamica per immagini e altro
self.addEventListener('fetch', event => {
  const requestUrl = new URL(event.request.url);

  // Se è richiesta una risorsa statica in cache statica (già gestita)
  if (urlsToCache.includes(requestUrl.pathname)) {
    event.respondWith(
      caches.match(event.request).then(cachedRes => cachedRes || fetch(event.request))
    );
    return;
  }

  // Cache dinamica per immagini nella cartella /static/upload/
  if (requestUrl.pathname.startsWith('/static/upload/')) {
    event.respondWith(
      caches.open(DYNAMIC_CACHE_NAME).then(cache =>
        fetch(event.request)
          .then(response => {
            cache.put(event.request, response.clone());
            return response;
          })
          .catch(() =>
            caches.match(event.request).then(cachedRes => cachedRes || caches.match('/offline.html'))
          )
      )
    );
    return;
  }

  // Fallback generico: prova fetch, altrimenti cache o offline.html
  event.respondWith(
    fetch(event.request)
      .catch(() =>
        caches.match(event.request).then(cachedRes => cachedRes || caches.match('/offline.html'))
      )
  );
});
