(function () {
  "use strict";

  const HELP = {
    uph_meta: {
      title: "UPH Meta",
      content:
        "UPH = Units Per Hour (peças por hora).\n\n" +
        "O que significa:\n" +
        "• Meta de produção por hora da linha.\n\n" +
        "Fórmulas úteis:\n" +
        "• Takt Time (s/peça) = 3600 / UPH Meta\n" +
        "• UPD Meta (peças/turno) = UPH Meta × Horas do turno\n\n" +
        "Como o sistema usa:\n" +
        "• Compara com UPH Real das operações.\n" +
        "• Se UPH Real < UPH Meta → marca como BALANCE."
    },

    hc_meta: {
      title: "HC Meta",
      content:
        "HC = Headcount (mão de obra).\n\n" +
        "O que significa:\n" +
        "• Quantidade de pessoas planejada para operar a linha.\n\n" +
        "Como o sistema usa:\n" +
        "• Soma o HC informado em cada operação (tabela).\n" +
        "• Compara com HC Meta e mostra status:\n" +
        "  - ACIMA (OVER) / FOLGA (UNDER) / OK."
    },

    perda_padrao: {
      title: "Perda padrão",
      content:
        "Perda padrão é a perda esperada do processo (paradas, microparadas, variação, etc.).\n\n" +
        "Formato:\n" +
        "• 0.10 = 10%\n" +
        "• 0.15 = 15%\n\n" +
        "Como o sistema usa:\n" +
        "• UPH Real = (3600 / TempoCiclo) × (1 - perda)\n" +
        "• Tempo alvo com perda (s/peça) = (3600 × (1 - perda)) / UPH Meta\n\n" +
        "Quanto maior a perda, menor o UPH Real."
    },

    horas_turno: {
      title: "Horas do turno",
      content:
        "Horas do turno em formato decimal (horas).\n\n" +
        "Exemplos:\n" +
        "• 8.30 = 8.3 horas (≈ 8h18m)\n" +
        "• 7.50 = 7.5 horas (7h30m)\n\n" +
        "Como o sistema usa:\n" +
        "• UPD = UPH × Horas do turno\n\n" +
        "Dica:\n" +
        "• Se quiser representar 8h30m exatos, use 8.5."
    }
  };

  function initHelpPopovers() {
    const buttons = document.querySelectorAll(".ts-info-btn[data-help-key]");
    if (!buttons.length) return;
    if (!window.bootstrap || !window.bootstrap.Popover) return;

    buttons.forEach((btn) => {
      const key = btn.getAttribute("data-help-key") || "";
      const item = HELP[key];
      if (!item) return;

      btn.setAttribute("data-bs-toggle", "popover");
      btn.setAttribute("data-bs-trigger", "focus");
      btn.setAttribute("data-bs-placement", "auto");
      btn.setAttribute("title", item.title);

      new window.bootstrap.Popover(btn, {
        container: "body",
        trigger: "focus",
        placement: "auto",
        html: false,
        title: item.title,
        content: item.content,
        customClass: "ts-popover"
      });
    });
  }

  document.addEventListener("DOMContentLoaded", initHelpPopovers);
})();
