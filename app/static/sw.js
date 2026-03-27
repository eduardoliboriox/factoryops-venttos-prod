/* FactoryOps Service Worker (safe by default)
   - Cacheia somente assets estáticos
   - Não cacheia páginas autenticadas
*/
const CACHE_VERSION = "factoryops-v1";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const STATIC_ASSETS = [
  "/offline",
  "/static/css/style.css",
  "/static/css/legal.css",
  "/static/css/auth.css",
  "/static/css/powerbi.css",
  "/static/css/solicitacoes.css",
  "/static/js/main.js",
  "/static/js/cookie-consent.js",
  "/static/js/pwa.js",
  "/static/images/logos/pwa-192.png",
  "/static/images/logos/pwa-512.png",
  "/static/images/logos/pwa-512-maskable.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys
          .filter((k) => {
            if (k === STATIC_CACHE) return false;
            return (
              k.startsWith("factoryops-") ||
              k.startsWith("smt-manager-") ||
              k.startsWith("workcost-")
            );
          })
          .map((k) => caches.delete(k))
      );
      await self.clients.claim();
    })()
  );
});

async function cacheFirst(req) {
  const cached = await caches.match(req);
  if (cached) return cached;
  const res = await fetch(req);
  const cache = await caches.open(STATIC_CACHE);
  cache.put(req, res.clone());
  return res;
}

async function navigationNetworkFirst(req) {
  try {
    const res = await fetch(req);
    return res;
  } catch (e) {
    const offline = await caches.match("/offline");
    return offline || new Response("Offline", { status: 503 });
  }
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  if (url.origin !== self.location.origin) return;

  if (req.mode === "navigate") {
    event.respondWith(navigationNetworkFirst(req));
    return;
  }

  if (url.pathname.startsWith("/static/")) {
    event.respondWith(cacheFirst(req));
    return;
  }

  if (url.pathname === "/sw.js" || url.pathname === "/manifest.webmanifest") {
    event.respondWith(
      (async () => {
        try {
          return await fetch(req);
        } catch (e) {
          const cached = await caches.match(req);
          return cached || new Response("", { status: 503 });
        }
      })()
    );
  }
});

self.addEventListener("push", (event) => {
  let payload = { title: "FactoryOps", body: "Nova notificação.", url: "/" };

  if (event.data) {
    try {
      payload = Object.assign(payload, JSON.parse(event.data.text()));
    } catch {
    }
  }

  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body,
      icon: "/static/images/logos/pwa-192.png",
      badge: "/static/images/logos/monochrome-badge-96x96.png",
      data: { url: payload.url || "/" },
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  const targetUrl = (event.notification.data && event.notification.data.url) || "/";

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
      for (const client of list) {
        if (client.url.includes(targetUrl) && "focus" in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
