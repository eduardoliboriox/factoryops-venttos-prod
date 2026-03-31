(function () {
  const btn = document.getElementById("install-app-btn");
  if (!btn) return;

  let deferredPrompt = null;

  function isIOS() {
    const ua = window.navigator.userAgent || "";
    const iOS = /iPad|iPhone|iPod/.test(ua);
    const iPadOS13Plus =
      /Macintosh/.test(ua) && typeof document !== "undefined" && "ontouchend" in document;
    return iOS || iPadOS13Plus;
  }

  function showBtn() {
    btn.classList.remove("d-none");
    btn.removeAttribute("aria-hidden");
  }

  function hideBtn() {
    btn.classList.add("d-none");
    btn.setAttribute("aria-hidden", "true");
  }

  // iOS não suporta beforeinstallprompt: mostramos o botão como "ajuda"
  if (isIOS()) {
    showBtn();

    btn.addEventListener("click", function () {
      try {
        if (window.bootstrap && window.bootstrap.Modal) {
          const modalEl = document.getElementById("pwaInstallHelpModal");
          if (modalEl) {
            window.bootstrap.Modal.getOrCreateInstance(modalEl).show();
            return;
          }
        }
      } catch (e) {}
      alert(
        'Para instalar no iPhone/iPad: toque em "Compartilhar" e depois em "Adicionar à Tela de Início".'
      );
    });

    return;
  }

  // Android/desktop (Chromium): capturamos o evento para permitir botão
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    showBtn();
  });

  window.addEventListener("appinstalled", () => {
    deferredPrompt = null;
    hideBtn();
  });

  btn.addEventListener("click", async function () {
    if (!deferredPrompt) return;

    try {
      deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;
      deferredPrompt = null;

      // Se aceitou, some com o botão (evita repetição)
      if (choice && choice.outcome === "accepted") {
        hideBtn();
      }
    } catch (e) {
      // Falha silenciosa para não quebrar login
    }
  });

  // default: escondido até ficar "installable"
  hideBtn();
})();
