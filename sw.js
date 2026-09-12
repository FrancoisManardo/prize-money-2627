/* Service worker : rend l'application utilisable hors ligne. */
const VERSION = 'a169233457';
const CACHE = 'prize-money-' + VERSION;
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-180.png',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(SHELL))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function putInCache(request, response){
  const copy = response.clone();
  caches.open(CACHE).then(c => c.put(request, copy)).catch(() => {});
  return response;
}

self.addEventListener('fetch', event => {
  const req = event.request;
  if(req.method !== 'GET') return;
  const url = new URL(req.url);

  // La page : réseau d'abord pour récupérer une mise à jour, cache en secours.
  if(req.mode === 'navigate' || url.pathname.endsWith('/index.html')){
    event.respondWith(
      fetch(req).then(r => putInCache(req, r))
        .catch(() => caches.match(req).then(r => r || caches.match('./index.html')))
    );
    return;
  }

  // Le reste, polices comprises : cache d'abord, réseau ensuite.
  event.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(r => putInCache(req, r)).catch(() => hit))
  );
});
