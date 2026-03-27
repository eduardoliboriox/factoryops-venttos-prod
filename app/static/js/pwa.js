(function () {
  if (!("serviceWorker" in navigator)) return;

  window.addEventListener("load", async function () {
    try {
      const swUrl = "/sw.js?v=" + encodeURIComponent(window.APP_VERSION || "dev");

      const reg = await navigator.serviceWorker.register(swUrl, { scope: "/" });

      if (reg && reg.waiting) {
      }
    } catch (e) {
    }
  });
})();
