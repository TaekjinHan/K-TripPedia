/**
 * HitoriOk Service Worker (커스텀)
 * 피드백 4번(A안): next-pwa 의존성 없이 패스 카드/저장 리스트만 캐시
 *
 * 캐시 전략:
 * - 패스 카드 관련 리소스: Cache First (오프라인 우선)
 * - API/데이터: Network First (최신 우선, 실패 시 캐시)
 * - 나머지 정적 리소스: Stale While Revalidate
 */

const CACHE_NAME = 'hitori-ok-v2';
const OFFLINE_URLS = [
    '/pass',
    '/saved',
];

// 설치: 핵심 페이지 프리캐시
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(OFFLINE_URLS);
        })
    );
    self.skipWaiting();
});

// 활성화: 이전 버전 캐시 정리
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys
                    .filter((key) => key !== CACHE_NAME)
                    .map((key) => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

// Fetch: 요청 유형별 전략 분기
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // 패스 카드 관련: Cache First
    if (url.pathname === '/pass' || url.pathname === '/saved') {
        event.respondWith(
            caches.match(event.request).then((cached) => {
                return cached || fetch(event.request).then((response) => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                    return response;
                });
            })
        );
        return;
    }

    // API 호출: Network First
    if (url.pathname.startsWith('/api') || url.hostname.includes('supabase')) {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
        return;
    }

    // 정적 리소스: Stale While Revalidate
    if (event.request.destination === 'style' ||
        event.request.destination === 'script' ||
        event.request.destination === 'font') {
        event.respondWith(
            caches.match(event.request).then((cached) => {
                const fetchPromise = fetch(event.request).then((response) => {
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, response.clone()));
                    return response;
                });
                return cached || fetchPromise;
            })
        );
        return;
    }
});
