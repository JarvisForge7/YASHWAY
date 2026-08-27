const CACHE_NAME = "yashway-v1";

const APP_SHELL = [
    "/",
    "/services",
    "/booking",
    "/track",
    "/static/css/style.css",
    "/static/js/script.js"
];


// ================================
// INSTALL
// ================================

self.addEventListener("install", (event) => {

    event.waitUntil(

        caches.open(CACHE_NAME)
            .then((cache) => {

                return cache.addAll(APP_SHELL);

            })

    );

    self.skipWaiting();

});


// ================================
// ACTIVATE
// ================================

self.addEventListener("activate", (event) => {

    event.waitUntil(

        caches.keys().then((cacheNames) => {

            return Promise.all(

                cacheNames.map((cacheName) => {

                    if (cacheName !== CACHE_NAME) {

                        return caches.delete(cacheName);

                    }

                })

            );

        })

    );

    self.clients.claim();

});


// ================================
// FETCH
// ================================

self.addEventListener("fetch", (event) => {

    const request = event.request;

    // फक्त GET requests handle करा
    if (request.method !== "GET") {
        return;
    }

    event.respondWith(

        fetch(request)

            .then((response) => {

                // नवीन response cache करा
                const responseClone = response.clone();

                caches.open(CACHE_NAME)
                    .then((cache) => {

                        cache.put(request, responseClone);

                    });

                return response;

            })

            .catch(() => {

                // Internet नसेल तर cache मधून
                return caches.match(request);

            })

    );

});