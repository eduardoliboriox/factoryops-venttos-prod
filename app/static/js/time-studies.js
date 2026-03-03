(function () {
  "use strict";

  window.TS = {
    studies: [],
    currentStudyId: null,
  };

  function documentFitRefresh() {
    try {
      window.dispatchEvent(new Event("documentfit:refresh"));
    } catch (e) {
      // noop
    }
  }

  window.showMsg = function showMsg(containerId, text, type = "success") {
    const el = document.getElementById(containerId);
    if (!el) return;

    if (!text) {
      el.innerHTML = "";
      return;
    }

    el.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show mb-2" role="alert">
        ${text}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
  };

  window.openPrintView = function openPrintView() {
    const id = Number(window.TS.currentStudyId || 0);
    if (!id) {
      window.showMsg("tsMsgOps", "Abra um estudo antes de imprimir.", "warning");
      return;
    }
    window.open(`/smt/estudo-tempo/print/${id}`, "_blank", "noopener");
  };

  const TS_LINHAS_FALLBACK = {
    IM: ["IM-01", "IM-02", "IM-03", "IM-04", "IM-05", "IM-06"],
    PA: ["IP-COM", "PA-01", "PA-03", "PA-04", "PA-07", "PA-08", "PA-09", "PA-13", "WIFI"],
    PTH: ["ADE-01", "AXI-01", "AXI-02", "AXI-03", "JUM-01", "JUM-02", "RAD-01", "RAD-02", "RAD-03", "ROU-01", "ROU-02", "ROU-03"],
    SMT: ["SMT-01", "SMT-02", "SMT-03", "SMT-04", "SMT-05", "SMT-06", "SMT-07", "SMT-08", "SMT-09"],
  };

  function renderLinhaOptions(linhas, keepValue = false) {
    const select = document.getElementById("tsLinhaSelect");
    if (!select) return;

    const prev = keepValue ? select.value : null;
    select.innerHTML = "";

    if (!Array.isArray(linhas) || !linhas.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "—";
      select.appendChild(opt);
      select.value = "";
      return;
    }

    linhas.forEach((l) => {
      const opt = document.createElement("option");
      opt.value = l;
      opt.textContent = l;
      select.appendChild(opt);
    });

    if (prev && linhas.includes(prev)) {
      select.value = prev;
    } else {
      select.value = linhas[0];
    }
  }

  async function fetchLinhasDoBanco(setor) {
    const resp = await fetch(`/api/production/lines?setor=${encodeURIComponent(setor)}`, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const data = await resp.json();
    if (!resp.ok || !data || !data.sucesso) return null;
    return Array.isArray(data.lines) ? data.lines : [];
  }

  async function refreshLinhasBySetor(setor, keepValue = false) {
    try {
      const linhas = await fetchLinhasDoBanco(setor);
      if (linhas && linhas.length) {
        renderLinhaOptions(linhas, keepValue);
        return;
      }
      renderLinhaOptions(TS_LINHAS_FALLBACK[setor] || [], keepValue);
    } catch (e) {
      renderLinhaOptions(TS_LINHAS_FALLBACK[setor] || [], keepValue);
    }
  }

  window.loadStudies = async function loadStudies() {
    window.showMsg("tsMsgCreate", "", "success");

    const resp = await fetch("/api/time-studies?limit=50", {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const data = await resp.json();

    window.TS.studies = Array.isArray(data) ? data : [];
    const sel = document.getElementById("studySelect");
    if (!sel) return;

    sel.innerHTML = "";
    window.TS.studies.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = `#${s.id} · ${s.produto} · UPH ${s.uph_meta} · ${s.linha || "—"} · ${new Date(s.created_at).toLocaleString()}`;
      sel.appendChild(opt);
    });

    if (!window.TS.studies.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "Nenhum estudo ainda";
      sel.appendChild(opt);
    }
  };

  async function createStudy(e) {
    e.preventDefault();

    const fd = new FormData(e.target);

    const resp = await fetch("/api/time-studies", {
      method: "POST",
      body: fd,
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    const data = await resp.json();

    if (!resp.ok || !data.sucesso) {
      window.showMsg("tsMsgCreate", data.erro || "Erro ao criar estudo", "danger");
      return;
    }

    window.showMsg("tsMsgCreate", `Estudo criado (#${data.study.id}).`, "success");

    e.target.reset();
    const setorEl = document.getElementById("tsSetorSelect");
    if (setorEl) await refreshLinhasBySetor(setorEl.value, false);

    await window.loadStudies();

    window.TS.currentStudyId = data.study.id;
    const sel = document.getElementById("studySelect");
    if (sel) sel.value = String(data.study.id);
    await window.openSelectedStudy();
  }

  window.openSelectedStudy = async function openSelectedStudy() {
    const sel = document.getElementById("studySelect");
    const studyId = Number((sel && sel.value) || 0);
    if (!studyId) return;
    await openStudy(studyId);
  };

  function escHtml(s) {
    return (s || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatSuggest(rec) {
    if (!rec || rec.status !== "BALANCE") return "";

    const target =
      rec.cycle_target_sec !== null && rec.cycle_target_sec !== undefined
        ? Number(rec.cycle_target_sec).toFixed(2)
        : null;

    const dsec =
      rec.delta_sec !== null && rec.delta_sec !== undefined
        ? Number(rec.delta_sec).toFixed(2)
        : null;

    const dpct =
      rec.delta_pct !== null && rec.delta_pct !== undefined
        ? Number(rec.delta_pct).toFixed(1)
        : null;

    const pf =
      rec.parallel_factor !== null && rec.parallel_factor !== undefined
        ? Number(rec.parallel_factor).toFixed(2)
        : null;

    const ps =
      rec.parallel_suggested !== null && rec.parallel_suggested !== undefined
        ? Number(rec.parallel_suggested)
        : null;

    return `
      <div class="ts-mini-help">
        <strong>Alvo c/ perda:</strong> ${target}s ·
        <strong>Reduzir:</strong> ${dsec}s (${dpct}%)<br>
        <strong>Ou paralelizar:</strong> ~${pf} postos → sugerir <strong>${ps}</strong>
      </div>
    `;
  }

  async function openStudy(studyId) {
    const resp = await fetch(`/api/time-studies/${studyId}`, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const data = await resp.json();

    if (!resp.ok || !data.sucesso) {
      window.showMsg("tsMsgOps", data.erro || "Erro ao abrir estudo", "danger");
      return;
    }

    window.TS.currentStudyId = studyId;

    const area = document.getElementById("studyArea");
    if (!area) return;

    area.classList.remove("d-none");

    const s = data.study || {};
    const totals = data.totals || {};
    const ops = data.operations || [];

    const tTitle = document.getElementById("studyTitle");
    const tSub = document.getElementById("studySubtitle");
    if (tTitle) tTitle.textContent = `${s.produto || "—"} · Estudo #${s.id}`;
    if (tSub) {
      tSub.textContent =
        `Cliente: ${s.cliente || "—"} · Linha: ${s.linha || "—"} · ` +
        `Perda: ${Number(s.perda_padrao || 0).toFixed(2)} · ` +
        `Turno: ${Number(s.horas_turno || 0).toFixed(2)}h`;
    }

    const kpiU = document.getElementById("kpiUphMeta");
    const kpiH = document.getElementById("kpiHcMeta");
    const kpiT = document.getElementById("kpiTaktTime");
    const kpiUdm = document.getElementById("kpiUpdMeta");
    const kpiOps = document.getElementById("kpiTotalOps");
    const kpiTempo = document.getElementById("kpiTotalTempo");

    if (kpiU) kpiU.textContent = totals.uph_meta ?? "—";
    if (kpiH) kpiH.textContent = totals.hc_meta ?? "—";

    const takt =
      totals.takt_time_sec !== null && totals.takt_time_sec !== undefined
        ? Number(totals.takt_time_sec).toFixed(2)
        : "—";
    if (kpiT) kpiT.textContent = takt;

    const cycleTarget =
      totals.cycle_target_sec !== null && totals.cycle_target_sec !== undefined
        ? Number(totals.cycle_target_sec).toFixed(2)
        : null;

    const perda =
      totals.perda_padrao !== null && totals.perda_padrao !== undefined
        ? Number(totals.perda_padrao).toFixed(2)
        : null;

    const noteEl = document.getElementById("kpiCycleTargetNote");
    if (noteEl) {
      if (cycleTarget) {
        noteEl.innerHTML = `<strong>Alvo c/ perda (${perda}):</strong> ${cycleTarget}s`;
      } else {
        noteEl.innerHTML = "";
      }
    }

    if (kpiUdm) kpiUdm.textContent = totals.upd_meta ?? "—";
    if (kpiOps) kpiOps.textContent = totals.total_ops ?? 0;
    if (kpiTempo) kpiTempo.textContent = (totals.total_tempo_sec ?? 0).toFixed(1);

    const summary = document.getElementById("balanceSummary");
    if (summary) {
      const bc = Number(totals.balance_count || 0);
      const bottleneck = Number(totals.line_uph_bottleneck || 0);
      const gap = Number(totals.line_gap_uph || 0);

      if (bc > 0 && Number(totals.uph_meta || 0) > 0) {
        summary.classList.remove("d-none");
        summary.innerHTML = `
          <div class="ts-muted mb-1"><strong>Resumo do Balanceamento</strong></div>
          <div style="font-size: 13px;">
            Operações em <strong>BALANCE:</strong> <strong>${bc}</strong> ·
            <strong>UPH gargalo da linha:</strong> <strong>${bottleneck}</strong> ·
            <strong>Gap vs meta:</strong> <strong>${gap}</strong> UPH
          </div>
        `;
      } else {
        summary.classList.add("d-none");
        summary.innerHTML = "";
      }
    }

    const tbody = document.getElementById("opsTableBody");
    if (!tbody) return;

    tbody.innerHTML = "";

    ops.forEach((op) => {
      const tr = document.createElement("tr");

      const bal = String(op.balance || "OK").trim().toUpperCase();
      if (bal === "BALANCE") tr.classList.add("ts-row-balance");

      const pillClass = bal === "OK" ? "ts-status-ok" : "ts-status-balance";
      const suggestHtml = bal === "BALANCE" ? formatSuggest(op.recommendation) : "";

      tr.innerHTML = `
        <td class="fw-bold">${op.ordem ?? ""}</td>
        <td class="ts-col-op">${escHtml(op.operacao || "")}</td>
        <td>${Number(op.tempo_ciclo_sec || 0).toFixed(2)}</td>
        <td>${op.posto_trabalho ?? ""}</td>
        <td>${Number(op.hc || 0).toFixed(2)}</td>
        <td class="fw-bold">${op.uph_real ?? 0}</td>
        <td>${op.upd ?? 0}</td>
        <td class="text-center">
          <span class="ts-status-pill ${pillClass}">${bal}</span>
          ${suggestHtml}
        </td>
        <td class="text-center">
          <button class="btn btn-sm btn-outline-danger" onclick="deleteOp(${op.id})">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    const nextN = ops.length ? Math.max(...ops.map((o) => Number(o.ordem || 0))) + 1 : 1;
    const nInput = document.querySelector('#formAddOp input[name="ordem"]');
    if (nInput) nInput.value = String(nextN);

    window.showMsg("tsMsgOps", "", "success");

    documentFitRefresh();
  }

  window.submitAddOp = async function submitAddOp() {
    const studyId = window.TS.currentStudyId;
    if (!studyId) return;

    const form = document.getElementById("formAddOp");
    if (!form) return;

    const fd = new FormData(form);

    const resp = await fetch(`/api/time-studies/${studyId}/operations`, {
      method: "POST",
      body: fd,
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    const data = await resp.json();

    if (!resp.ok || !data.sucesso) {
      window.showMsg("tsMsgOps", data.erro || "Erro ao salvar operação", "danger");
      return;
    }

    const modalEl = document.getElementById("modalAddOp");
    if (modalEl && window.bootstrap && window.bootstrap.Modal) {
      const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.hide();
    }

    form.reset();
    await openStudy(studyId);
  };

  window.deleteOp = async function deleteOp(opId) {
    if (!opId) return;

    const resp = await fetch(`/api/time-studies/operations/${opId}`, {
      method: "DELETE",
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    const data = await resp.json();

    if (!resp.ok || !data.sucesso) {
      window.showMsg("tsMsgOps", data.erro || "Erro ao excluir operação", "danger");
      return;
    }

    await openStudy(window.TS.currentStudyId);
  };

  window.deleteSelectedStudy = async function deleteSelectedStudy() {
    const sel = document.getElementById("studySelect");
    const studyId = Number((sel && sel.value) || 0);
    if (!studyId) return;

    const resp = await fetch(`/api/time-studies/${studyId}`, {
      method: "DELETE",
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    const data = await resp.json();

    if (!resp.ok || !data.sucesso) {
      window.showMsg("tsMsgCreate", data.erro || "Erro ao excluir estudo", "danger");
      return;
    }

    window.TS.currentStudyId = null;

    const area = document.getElementById("studyArea");
    if (area) area.classList.add("d-none");

    await window.loadStudies();
    window.showMsg("tsMsgCreate", `Estudo #${studyId} excluído.`, "success");

    documentFitRefresh();
  };

  document.addEventListener("DOMContentLoaded", async () => {
    const setor = document.getElementById("tsSetorSelect");
    if (setor) {
      await refreshLinhasBySetor(setor.value, true);
      setor.addEventListener("change", async () => {
        await refreshLinhasBySetor(setor.value, false);
      });
    }

    const formCreate = document.getElementById("formCreateStudy");
    if (formCreate) formCreate.addEventListener("submit", createStudy);

    await window.loadStudies();

    documentFitRefresh();
  });
})();
