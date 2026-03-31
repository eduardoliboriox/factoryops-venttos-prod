function safeNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function clampPercent(p) {
  const n = safeNumber(p);
  if (n < 0) return 0;
  if (n > 100) return 100;
  return n;
}

function formatBRL(v) {
  const n = safeNumber(v);
  return "R$ " + n.toFixed(2).replace(".", ",");
}

let extrasRankingCache = [];

function buildExecutiveSummary({
  abertas,
  realizadas,
  totalGasto,
  extrasProv,
  extrasReal,
  absPercent,
  linhas
}) {
  const direcaoGasto =
    extrasProv > 0
      ? (extrasReal > extrasProv ? "acima" : (extrasReal < extrasProv ? "abaixo" : "em linha"))
      : "em linha";

  const statusAbs =
    absPercent > 0 ? "atenção" : "estável";

  return `
    No período filtrado, foram registradas <strong>${abertas}</strong> solicitações abertas e
    <strong>${realizadas}</strong> solicitações realizadas.
    O gasto total estimado das realizadas é <strong>${formatBRL(totalGasto)}</strong>.
    Em extras, o realizado está <strong>${direcaoGasto}</strong> do provisionado
    (<strong>${formatBRL(extrasReal)}</strong> vs <strong>${formatBRL(extrasProv)}</strong>).
    Absenteísmo geral em <strong>${absPercent}%</strong> e <strong>${linhas}</strong> clientes ativos.
    Direcionamento: <strong>${statusAbs}</strong>.
  `.trim();
}

function renderTopClientes(clientes) {
  const ul = document.getElementById("topClientesList");
  if (!ul) return;

  ul.innerHTML = "";

  const top = (Array.isArray(clientes) ? clientes : [])
    .slice()
    .sort((a, b) => safeNumber(b.percentual) - safeNumber(a.percentual))
    .slice(0, 5);

  if (!top.length) {
    ul.innerHTML = `
      <li class="list-group-item text-muted">
        Sem dados para exibir com os filtros atuais.
      </li>
    `;
    return;
  }

  top.forEach((c, idx) => {
    ul.innerHTML += `
      <li class="list-group-item d-flex justify-content-between align-items-center">
        <span class="fw-semibold">${c.cliente || "-"}</span>
        <span class="badge bg-warning">${safeNumber(c.percentual).toFixed(2)}%</span>
      </li>
    `;
  });
}

function renderRankingUnidades(extras) {
  const container = document.querySelector("#rankingPowerBI");
  if (!container) return;

  container.innerHTML = "";
  extrasRankingCache = Array.isArray(extras) ? extras : [];

  const max = Math.max(...extrasRankingCache.map(x => safeNumber(x.percentual)), 1);

  extrasRankingCache.forEach(e => {
    const filial = e.filial || "-";
    const pct = safeNumber(e.percentual);

    container.innerHTML += `
      <div class="text-center" style="width:70px; cursor:pointer"
           onclick="abrirModalUnidadePowerBI('${filial}')">
        <div class="fw-bold small mb-1">${pct.toFixed(1)}%</div>
        <div style="
          height:${(pct * 180) / max}px;
          background:#0d6efd;
          border-radius:6px;">
        </div>
        <small class="d-block mt-1">${filial}</small>
      </div>
    `;
  });

  if (!extrasRankingCache.length) {
    container.innerHTML = `<div class="text-muted small mt-3">Sem dados para exibir.</div>`;
  }
}

function renderExecutiveBars({ extrasProv, extrasReal, abertas, realizadas }) {
  const barGasto = document.getElementById("bar-gasto");
  const barGastoLeft = document.getElementById("bar-gasto-left");
  const barGastoLabel = document.getElementById("bar-gasto-label");

  if (barGasto) {
    const denom = extrasProv > 0 ? extrasProv : (extrasReal > 0 ? extrasReal : 1);
    const pct = clampPercent((extrasReal / denom) * 100);

    barGasto.style.width = `${pct}%`;
    barGasto.classList.remove("bg-success", "bg-danger", "bg-warning");

    if (extrasProv <= 0 && extrasReal <= 0) {
      barGasto.classList.add("bg-secondary");
    } else if (extrasReal > extrasProv) {
      barGasto.classList.add("bg-warning");
    } else {
      barGasto.classList.add("bg-success");
    }
  }

  if (barGastoLeft) barGastoLeft.innerText = formatBRL(extrasReal);
  if (barGastoLabel) barGastoLabel.innerText = `${formatBRL(extrasReal)} / ${formatBRL(extrasProv)}`;

  const barSol = document.getElementById("bar-solicitacoes");
  const barSolLabel = document.getElementById("bar-solicitacoes-label");

  const total = safeNumber(abertas) + safeNumber(realizadas);
  const pctSol = total > 0 ? clampPercent((safeNumber(abertas) / total) * 100) : 0;

  if (barSol) barSol.style.width = `${pctSol}%`;
  if (barSolLabel) barSolLabel.innerText = `${abertas} / ${total}`;
}

function abrirModalUnidadePowerBI(filial) {
  const modalEl = document.getElementById("modalLinhaPowerBI");
  if (!modalEl) return;

  const tituloEl = document.getElementById("modalLinhaPowerBITitulo");
  const lista = document.getElementById("modalListaPowerBI");
  const totalSpan = document.getElementById("modalTotalPowerBI");

  if (!tituloEl || !lista || !totalSpan) return;

  const item = extrasRankingCache.find(x => (x.filial || "") === filial);

  tituloEl.innerText = `Extras — ${filial}`;
  lista.innerHTML = "";

  if (!item) {
    lista.innerHTML = `
      <li class="list-group-item text-muted">
        Nenhum dado para esta unidade.
      </li>
    `;
    totalSpan.innerText = "0";
  } else {
    const prov = safeNumber(item.provisionado);
    const real = safeNumber(item.realizado);

    lista.innerHTML += `
      <li class="list-group-item d-flex justify-content-between">
        % no período
        <span class="badge bg-primary">${safeNumber(item.percentual).toFixed(1)}%</span>
      </li>
      <li class="list-group-item d-flex justify-content-between">
        Provisionado
        <span class="badge bg-warning">${formatBRL(prov)}</span>
      </li>
      <li class="list-group-item d-flex justify-content-between">
        Realizado
        <span class="badge bg-success">${formatBRL(real)}</span>
      </li>
    `;

    totalSpan.innerText = formatBRL(real);
  }

  new bootstrap.Modal(modalEl).show();
}

async function atualizarPowerBI() {
  try {
    const params = new URLSearchParams({
      data_inicial: document.querySelector('[name="data_inicial"]').value,
      data_final: document.querySelector('[name="data_final"]').value,
      turno: document.querySelector('[name="turno"]').value || '',
      filial: document.querySelector('[name="filial"]').value || '',
      setor: document.querySelector('[name="setor"]')?.value || '',
      linha: document.querySelector('[name="linha"]')?.value || ''
    });

    const resp = await fetch(`/api/powerbi/resumo?${params}`);
    const data = await resp.json();

    const k = data?.kpis || {};
    const r = data?.rankings || {};

    document.querySelector("#kpi-solicitacoes-abertas").innerText =
      safeNumber(k.solicitacoes_abertas);

    document.querySelector("#kpi-solicitacoes-realizadas").innerText =
      safeNumber(k.solicitacoes_realizadas);

    document.querySelector("#kpi-total-gasto").innerText =
      formatBRL(k.total_gasto);

    document.querySelector("#kpi-extras-provisionado").innerText =
      formatBRL(k.extras_provisionado);

    document.querySelector("#kpi-extras-realizado").innerText =
      formatBRL(k.extras_realizado);

    document.querySelector("#kpi-abs").innerText =
      safeNumber(k.absenteismo).toFixed(1) + "%";

    const chipAbs = document.querySelector("#kpi-abs-chip");
    if (chipAbs) chipAbs.innerText = safeNumber(k.absenteismo).toFixed(1) + "%";

    const linhasEl = document.querySelector("#kpi-linhas");
    if (linhasEl) linhasEl.innerText = safeNumber(k.linhas);

    const summaryEl = document.getElementById("exec-summary-text");
    if (summaryEl) {
      summaryEl.innerHTML = buildExecutiveSummary({
        abertas: safeNumber(k.solicitacoes_abertas),
        realizadas: safeNumber(k.solicitacoes_realizadas),
        totalGasto: safeNumber(k.total_gasto),
        extrasProv: safeNumber(k.extras_provisionado),
        extrasReal: safeNumber(k.extras_realizado),
        absPercent: safeNumber(k.absenteismo).toFixed(1),
        linhas: safeNumber(k.linhas)
      });
    }

    renderExecutiveBars({
      extrasProv: safeNumber(k.extras_provisionado),
      extrasReal: safeNumber(k.extras_realizado),
      abertas: safeNumber(k.solicitacoes_abertas),
      realizadas: safeNumber(k.solicitacoes_realizadas)
    });

    renderTopClientes(r.clientes || []);
    renderRankingUnidades(r.extras || []);

  } catch (e) {
    console.error("Erro ao atualizar PowerBI", e);
  }
}

setInterval(atualizarPowerBI, 5000);
document.addEventListener("DOMContentLoaded", atualizarPowerBI);
