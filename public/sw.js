self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => self.clients.claim());

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // Never cache API calls — always go to network
  if (['/chat', '/save', '/history', '/new-session'].includes(url.pathname)) {
    e.respondWith(fetch(e.request));
    return;
  }
  // For everything else, network first, fall back to cache
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
