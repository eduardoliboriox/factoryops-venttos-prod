document.addEventListener("DOMContentLoaded", () => {

  const consent = localStorage.getItem("cookieConsent");

  if (consent === "all" || consent === "essential" || consent === "accepted") {
    return;
  }

  const banner = document.createElement("div");
  banner.className = "cookie-banner";

  banner.innerHTML = `
    <div class="cookie-content">
      Este site utiliza tecnologias como cookies para ativar funcionalidades essenciais do site, bem como para análise de dados, personalização e publicidade direcionada.
      <a href="/cookie-policy" target="_blank" rel="noopener noreferrer">Saiba mais</a>
    </div>
    <div class="cookie-actions">
      <button id="acceptCookies" class="btn btn-sm btn-primary">
        Aceitar
      </button>
      <button id="denyNonEssentialCookies" class="btn btn-sm btn-outline-secondary">
        Negar não essencial
      </button>
    </div>
  `;

  document.body.appendChild(banner);

  const acceptBtn = document.getElementById("acceptCookies");
  const denyBtn = document.getElementById("denyNonEssentialCookies");

  if (acceptBtn) {
    acceptBtn.addEventListener("click", () => {
      localStorage.setItem("cookieConsent", "all");
      banner.remove();
    });
  }

  if (denyBtn) {
    denyBtn.addEventListener("click", () => {
      localStorage.setItem("cookieConsent", "essential");
      banner.remove();
    });
  }

});
