(function () {
  "use strict";

  let currentStudyId = null;

  function qs(sel) {
    return document.querySelector(sel);
  }

  function escapeHtml(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function fmtNum(n, digits = 0) {
    const v = Number(n);
    if (!Number.isFinite(v)) return "—";
    return v.toFixed(digits);
  }

  function fmtDateTime(iso) {
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return "—";
      return d.toLocaleString();
    } catch {
      return "—";
    }
  }

  function setHtml(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function showMsg(containerId, kind, msg) {
    const safe = escapeHtml(msg || "");
    setHtml(
      containerId,
      `<div class="alert alert-${kind} py-2 mb-2">${safe}</div>`
    );
  }

  function clearMsg(containerId) {
    setHtml(containerId, "");
  }

  async function apiJson(url, options = {}) {
    const resp = await fetch(url, {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        ...(options.headers || {}),
      },
      ...options,
    });

    const data = await resp.json().catch(() => ({}));
    return { ok: resp.ok, status: resp.status, data };
  }

  async function loadLinesForSector(setor) {
    const linhaSelect = qs("#tsLinhaSelect");
    if (!linhaSelect) return;

    linhaSelect.innerHTML = "";
    const { ok, data } = await apiJson(`/api/production/lines?setor=${encodeURIComponent(setor || "")}`);
    const lines = (ok && data && data.lines) ? data.lines : [];

    if (!lines.length) {
      linhaSelect.innerHTML = `<option value="" selected>—</option>`;
      return;
    }

    for (const ln of lines) {
      const opt = document.createElement("option");
      opt.value = ln;
      opt.textContent = ln;
      linhaSelect.appendChild(opt);
    }
  }


  async function loadStudies() {
    const select = qs("#studySelect");
    if (!select) return;

    select.innerHTML = `<option value="">Carregando...</option>`;

    const { ok, data } = await apiJson("/api/time-studies?limit=50");
    if (!ok || !Array.isArray(data)) {
      select.innerHTML = `<option value="">Falha ao carregar</option>`;
      return;
    }

    if (data.length === 0) {
      select.innerHTML = `<option value="">Nenhum estudo encontrado</option>`;
      return;
    }

    select.innerHTML = "";
    for (const s of data) {
      const labelParts = [];
      labelParts.push(`#${s.id}`);
      if (s.produto) labelParts.push(`${s.produto}`);
      if (s.cliente) labelParts.push(`- ${s.cliente}`);
      if (s.uph_meta != null) labelParts.push(`· UPH ${s.uph_meta}`);
      if (s.linha) labelParts.push(`· ${s.linha}`);
      if (s.created_at) labelParts.push(`· ${fmtDateTime(s.created_at)}`);

      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = labelParts.join(" ");
      select.appendChild(opt);
    }
  }

  function renderHcPill(status) {
    const pill = qs("#kpiHcStatusPill");
    if (!pill) return;

    const st = String(status || "").toUpperCase();

    pill.classList.remove("d-none", "ts-pill-ok", "ts-pill-warn", "ts-pill-info");

    if (st === "OVER") {
      pill.textContent = "ACIMA";
      pill.classList.add("ts-pill", "ts-pill-warn");
      return;
    }

    if (st === "UNDER") {
      pill.textContent = "FOLGA";
      pill.classList.add("ts-pill", "ts-pill-info");
      return;
    }

    pill.textContent = "OK";
    pill.classList.add("ts-pill", "ts-pill-ok");
  }

  function renderStudy(detail) {
    const studyArea = qs("#studyArea");
    if (!studyArea) return;

    const study = detail.study || {};
    const totals = detail.totals || {};
    const ops = detail.operations || [];

    currentStudyId = Number(study.id || 0) || null;

    setText("studyTitle", `${study.produto || "—"} · Estudo #${study.id || "—"}`);
    setText(
      "studySubtitle",
      `Cliente: ${study.cliente || "—"} · Linha: ${study.linha || "—"} · Perda: ${fmtNum(totals.perda_padrao, 2)} · Turno: ${fmtNum(study.horas_turno, 2)}h`
    );

    setText("kpiUphMeta", totals.uph_meta != null ? String(totals.uph_meta) : "—");
    setText("kpiHcMeta", totals.hc_meta != null ? fmtNum(totals.hc_meta, 2) : "—");
    setText("kpiTaktTime", totals.takt_time_sec != null ? fmtNum(totals.takt_time_sec, 2) : "—");
    setText("kpiUpdMeta", totals.upd_meta != null ? String(totals.upd_meta) : "—");

    if (totals.cycle_target_sec != null) {
      setHtml(
        "kpiCycleTargetNote",
        `Alvo c/ perda (${fmtNum(totals.perda_padrao, 2)}): <strong>${fmtNum(totals.cycle_target_sec, 2)}s</strong>`
      );
    } else {
      setHtml("kpiCycleTargetNote", "");
    }

    setText("kpiLineUph", totals.line_uph_bottleneck != null ? String(totals.line_uph_bottleneck) : "—");
    setText("kpiLineUphNoLoss", totals.line_uph_bottleneck_no_loss != null ? String(totals.line_uph_bottleneck_no_loss) : "—");
    setText("kpiLineUphWithLoss", totals.line_uph_bottleneck != null ? String(totals.line_uph_bottleneck) : "—");

    if (totals.uph_meta && totals.line_gap_uph != null) {
      setHtml(
        "kpiLineGapNote",
        `Gap vs meta: <strong>${String(totals.line_gap_uph)}</strong> UPH`
      );
    } else {
      setHtml("kpiLineGapNote", "");
    }

    if (totals.line_loss_gap_uph != null) {
      setHtml(
        "kpiLossGapNote",
        `Perda derruba: <strong>${String(totals.line_loss_gap_uph)}</strong> UPH`
      );
    } else {
      setHtml("kpiLossGapNote", "");
    }

    setText("kpiHcUsed", totals.sum_hc_ops != null ? fmtNum(totals.sum_hc_ops, 2) : "—");
    renderHcPill(totals.hc_status);

    if (totals.hc_gap != null) {
      const gap = Number(totals.hc_gap);
      if (Number.isFinite(gap) && gap > 0.01) {
        setHtml("kpiHcGapNote", `Acima do HC meta por: <strong>${fmtNum(gap, 2)}</strong>`);
      } else if (Number.isFinite(gap) && gap < -0.01) {
        setHtml("kpiHcGapNote", `Folga vs HC meta: <strong>${fmtNum(Math.abs(gap), 2)}</strong>`);
      } else {
        setHtml("kpiHcGapNote", `Igual ao HC meta`);
      }
    } else {
      setHtml("kpiHcGapNote", "");
    }

    setText("kpiTotalOps", totals.total_ops != null ? String(totals.total_ops) : "—");
    setText("kpiTotalTempo", totals.total_tempo_sec != null ? fmtNum(totals.total_tempo_sec, 1) : "—");

    const balEl = qs("#balanceSummary");
    if (balEl) {
      const bal = Number(totals.balance_count || 0);
      const uphGap = Number(totals.line_gap_uph || 0);
      const uphBot = Number(totals.line_uph_bottleneck || 0);

      if (bal > 0 && Number(totals.uph_meta || 0) > 0) {
        balEl.classList.remove("d-none");
        balEl.innerHTML =
          `Resumo do Balanceamento<br>` +
          `Operações em <strong>BALANCE:</strong> <strong>${bal}</strong> · ` +
          `<strong>UPH gargalo da linha:</strong> <strong>${uphBot}</strong> · ` +
          `<strong>Gap vs meta:</strong> <strong>${uphGap}</strong> UPH`;
      } else {
        balEl.classList.add("d-none");
        balEl.innerHTML = "";
      }
    }

    // Table
    const tbody = qs("#opsTableBody");
    if (tbody) {
      tbody.innerHTML = "";

      for (const op of ops) {
        const bal = String(op.balance || "OK").toUpperCase();
        const tr = document.createElement("tr");
        if (bal === "BALANCE") tr.classList.add("ts-row-balance");

        const rec = op.recommendation || null;

        const pill =
          bal === "OK"
            ? `<span class="ts-status-pill ts-status-ok">OK</span>`
            : `<span class="ts-status-pill ts-status-balance">BALANCE</span>`;

        let recHtml = "";
        if (bal === "BALANCE" && rec && String(rec.status).toUpperCase() === "BALANCE") {
          const parts = [];
          if (rec.cycle_target_sec != null) parts.push(`<strong>Alvo c/ perda:</strong> ${fmtNum(rec.cycle_target_sec, 2)}s`);
          if (rec.delta_sec != null && rec.delta_pct != null) parts.push(`<strong>Reduzir:</strong> ${fmtNum(rec.delta_sec, 2)}s (${fmtNum(rec.delta_pct, 1)}%)`);
          if (rec.parallel_factor != null && rec.parallel_suggested != null) parts.push(`<strong>Ou paralelizar:</strong> ~${fmtNum(rec.parallel_factor, 2)} postos → sugerir <strong>${rec.parallel_suggested}</strong>`);
          recHtml = `<div class="ts-muted mt-1" style="font-size:12px; line-height:1.25;">${parts.join("<br>")}</div>`;
        }

        tr.innerHTML = `
          <td><strong>${escapeHtml(op.ordem)}</strong></td>
          <td class="ts-col-op">${escapeHtml(op.operacao)}</td>
          <td>${fmtNum(op.tempo_ciclo_sec, 2)}</td>
          <td>${escapeHtml(op.posto_trabalho)}</td>
          <td>${fmtNum(op.hc, 2)}</td>
          <td><strong>${escapeHtml(op.uph_real)}</strong></td>
          <td>${escapeHtml(op.upd)}</td>
          <td>${pill}${recHtml}</td>
          <td>
            <button class="btn btn-outline-danger btn-sm" type="button" data-opid="${op.id}">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      }
    }

    tbody?.querySelectorAll("button[data-opid]")?.forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = Number(btn.getAttribute("data-opid") || 0);
        if (!id) return;
        if (!confirm("Excluir esta operação?")) return;

        clearMsg("tsMsgOps");
        const { ok, data } = await apiJson(`/api/time-studies/operations/${id}`, { method: "DELETE" });
        if (!ok || !data || data.sucesso !== true) {
          showMsg("tsMsgOps", "danger", (data && data.erro) ? data.erro : "Erro ao excluir operação");
          return;
        }

        await openSelectedStudy();
      });
    });

    studyArea.classList.remove("d-none");

    // Recalcula o document-fit após tornar a área visível no mobile
    requestAnimationFrame(() => {
      if (typeof window.applyDocumentFit === "function") {
        window.applyDocumentFit();
      }
    });
  }

  async function openSelectedStudy() {
    const select = qs("#studySelect");
    const studyId = Number(select?.value || 0);
    if (!studyId) {
      showMsg("tsMsgOps", "warning", "Selecione um estudo.");
      return;
    }

    clearMsg("tsMsgOps");

    const { ok, data } = await apiJson(`/api/time-studies/${studyId}`);
    if (!ok || !data || data.sucesso !== true) {
      showMsg("tsMsgOps", "danger", (data && data.erro) ? data.erro : "Erro ao abrir estudo");
      return;
    }

    renderStudy(data);
  }

  async function deleteSelectedStudy() {
    const select = qs("#studySelect");
    const studyId = Number(select?.value || 0);
    if (!studyId) return;

    if (!confirm("Excluir este estudo? Isso removerá também as operações.")) return;

    const { ok, data } = await apiJson(`/api/time-studies/${studyId}`, { method: "DELETE" });
    if (!ok || !data || data.sucesso !== true) {
      alert((data && data.erro) ? data.erro : "Erro ao excluir estudo");
      return;
    }

    currentStudyId = null;
    qs("#studyArea")?.classList.add("d-none");
    await loadStudies();
  }

  function openPrintView() {
    if (!currentStudyId) return;
    window.open(`/smt/estudo-tempo/print/${currentStudyId}`, "_blank");
  }

  async function onCreateStudySubmit(ev) {
    ev.preventDefault();
    clearMsg("tsMsgCreate");

    const form = ev.currentTarget;
    const fd = new FormData(form);

    const { ok, data } = await apiJson("/api/time-studies", { method: "POST", body: fd });
    if (!ok || !data || data.sucesso !== true) {
      showMsg("tsMsgCreate", "danger", (data && data.erro) ? data.erro : "Erro ao criar estudo");
      return;
    }

    showMsg("tsMsgCreate", "success", "Estudo criado com sucesso.");
    form.reset();

    const setor = qs("#tsSetorSelect");
    if (setor) setor.value = "SMT";

    await loadLinesForSector("SMT");
    await loadStudies();

    const created = data.study || {};
    const select = qs("#studySelect");
    if (select && created.id) {
      select.value = String(created.id);
      await openSelectedStudy();
    }
  }

  async function submitAddOp() {
    clearMsg("tsMsgOps");

    if (!currentStudyId) {
      showMsg("tsMsgOps", "warning", "Abra um estudo antes de adicionar operação.");
      return;
    }

    const form = qs("#formAddOp");
    if (!form) return;

    const fd = new FormData(form);

    const { ok, data } = await apiJson(`/api/time-studies/${currentStudyId}/operations`, { method: "POST", body: fd });
    if (!ok || !data || data.sucesso !== true) {
      showMsg("tsMsgOps", "danger", (data && data.erro) ? data.erro : "Erro ao adicionar operação");
      return;
    }

    const modalEl = qs("#modalAddOp");
    if (modalEl && window.bootstrap) {
      const inst = window.bootstrap.Modal.getInstance(modalEl) || new window.bootstrap.Modal(modalEl);
      inst.hide();
    }

    form.reset();
    const ordem = form.querySelector('[name="ordem"]');
    if (ordem) ordem.value = "1";
    const posto = form.querySelector('[name="posto_trabalho"]');
    if (posto) posto.value = "1";
    const hc = form.querySelector('[name="hc"]');
    if (hc) hc.value = "1.00";

    await openSelectedStudy();
  }


  document.addEventListener("DOMContentLoaded", async () => {
    const formCreate = qs("#formCreateStudy");
    if (formCreate) formCreate.addEventListener("submit", onCreateStudySubmit);

    const setorSel = qs("#tsSetorSelect");
    if (setorSel) {
      setorSel.addEventListener("change", async () => {
        await loadLinesForSector(setorSel.value);
      });
    }

    await loadLinesForSector("SMT");
    await loadStudies();
  });

  window.loadStudies = loadStudies;
  window.openSelectedStudy = openSelectedStudy;
  window.deleteSelectedStudy = deleteSelectedStudy;
  window.openPrintView = openPrintView;
  window.submitAddOp = submitAddOp;
})();
