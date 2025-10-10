const CACHE_NAME = 'flood-alert-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/dashboard.html',
  '/style.css',
  '/js/script.js',
  '/images/chirag.jpg',
  '/images/Pratham.jpg',
  '/images/shreyansh.jpg',
  '/images/Suryansh.jpg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
