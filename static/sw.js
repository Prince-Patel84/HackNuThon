const CACHE_NAME = 'industrial-docs-v1';
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';

// Resources to cache immediately
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/script.js',
    '/static/sw.js',
    '/static/qrcodes/',
    '/static/images/',
    '/static/fonts/',
    '/templates/index.html',
    '/templates/error.html'
];

// Install event - cache static resources
self.addEventListener('install', event => {
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE)
                .then(cache => cache.addAll(urlsToCache)),
            caches.open(DYNAMIC_CACHE)
                .then(cache => cache.addAll([
                    '/static/images/file-icon.png',
                    '/static/images/folder-icon.png',
                    '/static/images/logo.png'
                ]))
        ])
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Fetch event - handle offline requests
self.addEventListener('fetch', event => {
    // Skip cross-origin requests
    if (!event.request.url.startsWith(self.location.origin)) {
        return;
    }

    // Handle API requests differently
    if (event.request.url.includes('/api/')) {
        event.respondWith(handleApiRequest(event.request));
        return;
    }

    // Handle static resources
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached response if found
                if (response) {
                    return response;
                }

                // Clone the request
                const fetchRequest = event.request.clone();

                // Make network request
                return fetch(fetchRequest)
                    .then(response => {
                        // Check if valid response
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone the response
                        const responseToCache = response.clone();

                        // Cache the response
                        caches.open(DYNAMIC_CACHE)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    })
                    .catch(() => {
                        // If offline and resource not in cache, return offline fallback
                        if (event.request.mode === 'navigate') {
                            return caches.match('/templates/offline.html');
                        }
                        return null;
                    });
            })
    );
});

// Handle API requests
async function handleApiRequest(request) {
    try {
        // Try network first
        const networkResponse = await fetch(request);
        return networkResponse;
    } catch (error) {
        // If offline, try cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // If no cache, return offline response
        return new Response(JSON.stringify({
            status: 'offline',
            message: 'You are currently offline. Some features may be limited.'
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Handle background sync
self.addEventListener('sync', event => {
    if (event.tag === 'syncFiles') {
        event.waitUntil(syncFiles());
    }
});

// Sync files when back online
async function syncFiles() {
    // Implementation for syncing offline changes
    // This would be implemented when we add offline storage
    console.log('Syncing files...');
} 