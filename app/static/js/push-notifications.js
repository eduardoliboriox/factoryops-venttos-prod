(function () {
  "use strict";

  const STORAGE_KEY = "smt_push_state";

  function getState() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function setState(patch) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(Object.assign(getState(), patch)));
    } catch {
    }
  }

  function isPushSupported() {
    return (
      "serviceWorker" in navigator &&
      "PushManager" in window &&
      "Notification" in window
    );
  }

  function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const rawData = atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; i++) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  async function fetchVapidKey() {
    try {
      const resp = await fetch("/api/push/vapid-public-key", {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!resp.ok) return null;
      const data = await resp.json();
      return data.sucesso ? data.key : null;
    } catch {
      return null;
    }
  }

  async function sendSubscriptionToServer(subscription) {
    const payload = subscription.toJSON();
    try {
      const resp = await fetch("/api/push/subscribe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({
          endpoint: payload.endpoint,
          keys: payload.keys,
        }),
      });
      return resp.ok;
    } catch {
      return false;
    }
  }

  async function removeSubscriptionFromServer(endpoint) {
    try {
      await fetch("/api/push/unsubscribe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ endpoint }),
      });
    } catch {
    }
  }

  async function subscribe() {
    if (!isPushSupported()) return false;

    const permission = await Notification.requestPermission();
    if (permission !== "granted") return false;

    const vapidKey = await fetchVapidKey();
    if (!vapidKey) return false;

    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey),
      });

      const ok = await sendSubscriptionToServer(subscription);
      if (ok) setState({ subscribed: true });
      return ok;
    } catch {
      return false;
    }
  }

  async function unsubscribe() {
    if (!isPushSupported()) return;

    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        await removeSubscriptionFromServer(subscription.endpoint);
        await subscription.unsubscribe();
      }
      setState({ subscribed: false });
    } catch {
    }
  }

  async function autoSubscribeIfEligible() {
    if (!isPushSupported()) return;
    if (Notification.permission === "denied") return;

    const state = getState();
    if (state.subscribed) return;
    if (state.dismissed) return;

    const vapidKey = await fetchVapidKey();
    if (!vapidKey) return;

    if (Notification.permission === "granted") {
      await subscribe();
      return;
    }

    showPromptBanner();
  }

  function showPromptBanner() {
    if (document.getElementById("smt-push-banner")) return;

    const banner = document.createElement("div");
    banner.id = "smt-push-banner";
    banner.style.cssText = [
      "position:fixed",
      "bottom:72px",
      "left:50%",
      "transform:translateX(-50%)",
      "background:#0f172a",
      "color:#fff",
      "border-radius:14px",
      "padding:12px 16px",
      "display:flex",
      "align-items:center",
      "gap:12px",
      "z-index:9000",
      "box-shadow:0 8px 24px rgba(0,0,0,0.30)",
      "max-width:90vw",
      "font-size:14px",
    ].join(";");

    banner.innerHTML = `
      <span style="flex:1;">🔔 Ativar notificações de metas e estudos?</span>
      <button id="smt-push-allow"
              style="background:#3b82f6;color:#fff;border:none;border-radius:8px;padding:6px 14px;font-weight:700;cursor:pointer;white-space:nowrap;">
        Ativar
      </button>
      <button id="smt-push-dismiss"
              style="background:transparent;color:rgba(255,255,255,0.6);border:none;font-size:18px;cursor:pointer;line-height:1;padding:0 4px;">
        ×
      </button>
    `;

    document.body.appendChild(banner);

    document.getElementById("smt-push-allow").addEventListener("click", async () => {
      banner.remove();
      await subscribe();
    });

    document.getElementById("smt-push-dismiss").addEventListener("click", () => {
      banner.remove();
      setState({ dismissed: true });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.ready.then(() => {
        autoSubscribeIfEligible();
      });
    }
  });

  window.smtPush = { subscribe, unsubscribe };
})();
