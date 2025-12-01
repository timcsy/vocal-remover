/*! coi-serviceworker - 最小化版本：只注入 headers，不緩存 */
let coepCredentialless = false;

if (typeof window === 'undefined') {
  // Service Worker 環境
  self.addEventListener("install", () => self.skipWaiting());
  self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

  self.addEventListener("fetch", function (e) {
    const r = e.request;
    if (r.cache === "only-if-cached" && r.mode !== "same-origin") {
      return;
    }

    const request =
      coepCredentialless && r.mode === "no-cors"
        ? new Request(r, { credentials: "omit" })
        : r;

    e.respondWith(
      fetch(request)
        .then((response) => {
          if (response.status === 0) {
            return response;
          }

          const newHeaders = new Headers(response.headers);
          newHeaders.set("Cross-Origin-Embedder-Policy", coepCredentialless ? "credentialless" : "require-corp");
          newHeaders.set("Cross-Origin-Opener-Policy", "same-origin");

          return new Response(response.body, {
            status: response.status,
            statusText: response.statusText,
            headers: newHeaders,
          });
        })
        .catch((err) => console.error(err))
    );
  });
} else {
  // 瀏覽器環境
  (() => {
    // 已經是跨域隔離狀態，不需要做任何事
    if (window.crossOriginIsolated) {
      return;
    }

    // 檢查是否已經重新載入過
    const reloadedBySelf = window.sessionStorage.getItem("coiReloadedBySelf");
    window.sessionStorage.removeItem("coiReloadedBySelf");

    if (reloadedBySelf === "true") {
      // 已經重新載入過但還是沒有 crossOriginIsolated，可能是瀏覽器不支援
      console.warn("COI Service Worker: 重新載入後仍無法啟用 SharedArrayBuffer");
      return;
    }

    // 註冊 Service Worker
    navigator.serviceWorker.register(window.document.currentScript.src).then(
      (registration) => {
        // 等待 Service Worker 變成 active 狀態
        const waitForActive = () => {
          if (registration.active) {
            // Service Worker 已經 active，重新載入頁面
            window.sessionStorage.setItem("coiReloadedBySelf", "true");
            window.location.reload();
          }
        };

        // 如果已經 active 且沒有 controller，立即重新載入
        if (registration.active && !navigator.serviceWorker.controller) {
          waitForActive();
          return;
        }

        // 如果正在安裝中，等待安裝完成
        if (registration.installing) {
          registration.installing.addEventListener("statechange", function () {
            if (this.state === "activated") {
              waitForActive();
            }
          });
          return;
        }

        // 如果正在等待中，等待變成 active
        if (registration.waiting) {
          registration.waiting.addEventListener("statechange", function () {
            if (this.state === "activated") {
              waitForActive();
            }
          });
          return;
        }
      },
      (err) => console.error("COI Service Worker registration failed:", err)
    );
  })();
}
