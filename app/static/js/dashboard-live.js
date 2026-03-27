let dashboardIsLoading = false;
let dashboardTimeout = null;

let absenteismoPorDataCache = [];

function showDashboardLoading() {
  const overlay = document.getElementById("dashboardLoadingOverlay");
  if (overlay) overlay.classList.remove("d-none");
}

function hideDashboardLoading() {
  const overlay = document.getElementById("dashboardLoadingOverlay");
  if (overlay) overlay.classList.add("d-none");
}

function debounceDashboardUpdate(callback, delay = 400) {
  clearTimeout(dashboardTimeout);
  dashboardTimeout = setTimeout(callback, delay);
}

async function atualizarDashboard() {
  if (dashboardIsLoading) return;

  dashboardIsLoading = true;
  showDashboardLoading();

  try {
    const params = new URLSearchParams({
      data_inicial: document.querySelector('[name="data_inicial"]').value,
      data_final: document.querySelector('[name="data_final"]').value,
      turno: document.querySelector('[name="turno"]').value || '',
      filial: document.querySelector('[name="filial"]').value || ''
    });

    const [
      respResumo,
      respSolicitacoes,
      respExtras,
      respObjetivos,
      respClientes,
      respTipos,
      respAbsData,
      respProvisaoTipos
    ] = await Promise.all([
      fetch(`/api/dashboard/resumo?${params}`),
      fetch(`/api/dashboard/solicitacoes-resumo?${params}`),
      fetch(`/api/dashboard/extras?${params}`),
      fetch(`/api/dashboard/objetivos?${params}`),
      fetch(`/api/dashboard/clientes?${params}`),
      fetch(`/api/dashboard/tipos-solicitacao?${params}`),
      fetch(`/api/dashboard/absenteismo-por-data?${params}`),
      fetch(`/api/dashboard/provisao-tipos?${params}`)
    ]);

    const dataResumo = await respResumo.json();
    const dataSolicitacoes = await respSolicitacoes.json();
    const rankingExtras = await respExtras.json();
    const rankingObjetivos = await respObjetivos.json();
    const rankingClientes = await respClientes.json();
    const rankingTipos = await respTipos.json();
    const rankingAbsData = await respAbsData.json();
    const rankingProvisaoTipos = await respProvisaoTipos.json();

    document.getElementById("kpi-abs").innerText =
      dataResumo.kpis.absenteismo + "%";

    document.getElementById("kpi-linhas").innerText =
      dataResumo.kpis.linhas;

    document.getElementById("kpi-solicitacoes-abertas").innerText =
      dataSolicitacoes.abertas;

    document.getElementById("kpi-solicitacoes-fechadas").innerText =
      dataSolicitacoes.fechadas;

    document.getElementById("kpi-total-gasto").innerText =
      "R$ " + dataSolicitacoes.total_gasto
        .toFixed(2)
        .replace(".", ",");

    atualizarTabelaExtras(rankingExtras);
    atualizarObjetivos(rankingObjetivos);
    atualizarClientes(rankingClientes);
    atualizarTipos(rankingTipos);
    atualizarAbsenteismoPorData(rankingAbsData);

    atualizarTiposProvisao(rankingProvisaoTipos);

  } catch (e) {
    console.error("Erro ao atualizar dashboard", e);
  } finally {
    dashboardIsLoading = false;
    hideDashboardLoading();
  }
}

function atualizarClientes(dados) {
  const lista = document.getElementById("rankingClientesList");
  if (!lista) return;

  lista.innerHTML = "";

  dados.forEach(c => {
    lista.innerHTML += `
      <li class="list-group-item d-flex justify-content-between">
        ${c.cliente}
        <span class="badge bg-warning">${c.percentual}%</span>
      </li>
    `;
  });
}

function atualizarTabelaExtras(dados) {
  const tbody = document.querySelector("#rankingExtrasBody");
  if (!tbody) return;

  tbody.innerHTML = "";

  dados.forEach(f => {
    tbody.innerHTML += `
      <tr>
        <td class="fw-semibold">${f.filial}</td>
        <td><span class="badge bg-primary">${f.percentual}%</span></td>
        <td class="text-warning fw-bold">R$ ${f.provisionado.toFixed(2)}</td>
        <td class="text-success fw-bold">R$ ${f.realizado.toFixed(2)}</td>
      </tr>
    `;
  });
}

function atualizarObjetivos(dados) {
  const lista = document.getElementById("rankingObjetivosList");
  if (!lista) return;

  lista.innerHTML = "";

  dados.forEach(o => {
    lista.innerHTML += `
      <li class="list-group-item d-flex justify-content-between">
        ${o.status}
        <span class="badge bg-danger">${o.percentual}%</span>
      </li>
    `;
  });
}

function atualizarTipos(dados) {
  const lista = document.getElementById("rankingTiposList");
  if (!lista) return;

  lista.innerHTML = "";

  dados.forEach(t => {
    lista.innerHTML += `
      <li class="list-group-item d-flex justify-content-between">
        ${t.tipo}
        <span class="badge bg-info">${t.percentual}%</span>
      </li>
    `;
  });
}

function atualizarAbsenteismoPorData(dados) {
  absenteismoPorDataCache = Array.isArray(dados) ? dados : [];

  const lista = document.getElementById("rankingAbsenteismoDataList");
  const btn = document.getElementById("toggleDatasBtn");

  if (!lista) return;

  lista.innerHTML = "";

  absenteismoPorDataCache.forEach((d, index) => {

    const dataFormatada =
      new Date(d.data).toLocaleDateString("pt-BR");

    lista.innerHTML += `
      <li class="list-group-item d-flex justify-content-between
          ${index >= 5 ? 'd-none extra-data' : ''}"
          style="cursor:pointer"
          onclick="abrirModalAbsenteismo('${d.data}')">
        <span>${dataFormatada}</span>
        <span class="badge bg-danger">${d.qtd}</span>
      </li>
    `;
  });

  if (btn) {
    if (absenteismoPorDataCache.length > 5) {
      btn.classList.remove("d-none");
      btn.innerText = "Ver mais";
    } else {
      btn.classList.add("d-none");
    }
  }
}

function atualizarTiposProvisao(dados) {
  const lista = document.getElementById("rankingGastosList");
  const btn = document.getElementById("toggleGastosBtn");

  if (!lista) return;

  const itens = Array.isArray(dados) ? dados : [];
  lista.innerHTML = "";

  if (!itens.length) {
    lista.innerHTML = `
      <li class="list-group-item text-muted d-flex justify-content-between">
        Nenhuma provisão encontrada
        <span class="badge bg-secondary">0</span>
      </li>
    `;
    if (btn) btn.classList.add("d-none");
    return;
  }

  itens.forEach((g, index) => {
    const tipo = g.tipo || "";
    const pct = Number(g.percentual || 0);
    const total = Number(g.total || 0);

    lista.innerHTML += `
      <li class="list-group-item d-flex justify-content-between
          ${index >= 6 ? 'd-none extra-gasto' : ''}">
        <span>
          ${tipo}
          <span class="badge bg-primary ms-2">${pct}%</span>
        </span>
        <span class="fw-bold text-success">
          R$ ${total.toFixed(2).replace(".", ",")}
        </span>
      </li>
    `;
  });

  if (btn) {
    if (itens.length > 6) {
      btn.classList.remove("d-none");
      btn.innerText = "Ver mais";
    } else {
      btn.classList.add("d-none");
    }
  }
}

async function abrirModalAbsenteismo(dataISO) {

  const modalEl = document.getElementById("modalAbsenteismo");
  if (!modalEl) return;

  const tituloEl = document.getElementById("modalAbsDataTitulo");
  const tbody = document.getElementById("modalAbsTabelaBody");
  const totalEl = document.getElementById("modalAbsTotal");

  if (!tituloEl || !tbody || !totalEl) return;

  const item = absenteismoPorDataCache.find(x => x.data === dataISO);

  const dataFormatada = new Date(dataISO).toLocaleDateString("pt-BR");
  tituloEl.innerText = `Faltas — ${dataFormatada}`;

  tbody.innerHTML = "";

  if (!item || !Array.isArray(item.funcionarios) || !item.funcionarios.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="3" class="text-muted text-center">
          Nenhuma falta registrada
        </td>
      </tr>
    `;
    totalEl.innerText = "0";
  } else {
    let total = 0;

    item.funcionarios.forEach(f => {
      const matricula = f.matricula || "";
      const nome = f.nome || "";
      const qtd = Number(f.total || 0);

      total += qtd;

      tbody.innerHTML += `
        <tr>
          <td class="text-nowrap">${matricula}</td>
          <td>${nome}</td>
          <td class="text-end">
            <span class="badge bg-danger">${qtd}</span>
          </td>
        </tr>
      `;
    });

    totalEl.innerText = String(total);
  }

  new bootstrap.Modal(modalEl).show();
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("dashboardFilters");
  if (!form) return;

  form.querySelectorAll("input, select").forEach(el => {
    el.addEventListener("change", () => {
      debounceDashboardUpdate(() => atualizarDashboard());
    });
  });

  atualizarDashboard();
});

setInterval(() => {
  if (!dashboardIsLoading) {
    atualizarDashboard();
  }
}, 10000);
