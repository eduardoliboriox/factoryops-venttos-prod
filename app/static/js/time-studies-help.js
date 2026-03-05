(function () {
  "use strict";

  const HELP = {
    uph_meta: {
      title: "UPH Meta",
      body: "Unidades Por Hora — quantidade de peças que a linha deve produzir em 1 hora. Fórmula de referência: UPH = 3600 / Tempo de Ciclo (s). Define o ritmo esperado da operação."
    },
    hc_meta: {
      title: "HC Meta",
      body: "Head Count Meta — número de operadores planejados para atingir o UPH Meta. Usado para comparar com o HC real alocado nas operações do estudo."
    },
    perda_padrao: {
      title: "Perda Padrão",
      body: "Fator de ineficiência operacional esperado. Exemplo: 0.10 = 10% de perda. Fórmula: UPH Real = (3600 / Tempo Ciclo) × (1 − Perda). Inclui microparadas, variações de ritmo e ajustes."
    },
    horas_turno: {
      title: "Horas do Turno",
      body: "Duração do turno de produção em horas. Usado para calcular o UPD (Unidades Por Dia): UPD = UPH × Horas do Turno. Exemplo: 8.30 representa 8 horas e 30 minutos."
    }
  };

  function buildModal() {
    if (document.getElementById("tsHelpModal")) return;

    const div = document.createElement("div");
    div.innerHTML =
      '<div class="modal fade" id="tsHelpModal" tabindex="-1" aria-hidden="true">' +
        '<div class="modal-dialog modal-dialog-centered">' +
          '<div class="modal-content">' +
            '<div class="modal-header py-2 px-3">' +
              '<h6 class="modal-title fw-bold mb-0" id="tsHelpModalTitle"></h6>' +
              '<button type="button" class="btn-close btn-sm" data-bs-dismiss="modal"></button>' +
            '</div>' +
            '<div class="modal-body px-3 py-3" id="tsHelpModalBody" style="font-size:14px;line-height:1.6;"></div>' +
          '</div>' +
        '</div>' +
      '</div>';

    document.body.appendChild(div.firstChild);
  }

  function openHelp(key) {
    const info = HELP[key];
    if (!info) return;

    const titleEl = document.getElementById("tsHelpModalTitle");
    const bodyEl  = document.getElementById("tsHelpModalBody");
    if (!titleEl || !bodyEl) return;

    titleEl.textContent = info.title;
    bodyEl.textContent  = info.body;

    const modalEl = document.getElementById("tsHelpModal");
    if (!modalEl || !window.bootstrap) return;

    const inst = window.bootstrap.Modal.getOrCreateInstance(modalEl);
    inst.show();
  }

  document.addEventListener("DOMContentLoaded", function () {
    buildModal();

    document.querySelectorAll("[data-ts-help]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        openHelp(btn.getAttribute("data-ts-help"));
      });
    });
  });
})();
