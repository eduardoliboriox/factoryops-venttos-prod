"use strict";

// URLs injetadas pelo template via atributos data no elemento #planejamento-root
const _root        = () => document.getElementById("planejamento-root");
const URL_CRIAR    = () => _root().dataset.urlCriar;
const URL_PLANO    = () => _root().dataset.urlPlano;
const URL_DETALHE  = () => _root().dataset.urlDetalhe;
const URL_META     = () => _root().dataset.urlMeta;
const URL_EDITAR_TPL  = () => _root().dataset.urlEditarTpl;
const URL_STATUS_TPL  = () => _root().dataset.urlStatusTpl;
const URL_EXCLUIR_TPL = () => _root().dataset.urlExcluirTpl;

const OPS_JSON     = () => JSON.parse(_root().dataset.ops    || "[]");
const OPCOES_LINHA = () => JSON.parse(_root().dataset.opcoes || "{}");

// ─── Setup sugerido por setor/linha ──────────────────────────────────────────
function calcularSetupSugerido(setor, linha) {
  const s = (setor || "").toUpperCase();
  const l = (linha || "").toUpperCase();
  if (s === "PTH" && l.startsWith("ROU")) return 20;
  if (s === "IM" || s === "PA")          return 30;
  if (s === "SMD" || s === "SMT")        return 60;
  return 0;
}

// ─── Filtro dinâmico de linhas ────────────────────────────────────────────────
function onSetorChange(setor, selectLinhaId) {
  const sel    = document.getElementById(selectLinhaId);
  const opcoes = OPCOES_LINHA();
  const linhas = setor ? (opcoes[setor] || []) : Object.values(opcoes).flat();

  const atual = sel.value;
  sel.innerHTML = '<option value="">Todas as linhas</option>';
  linhas.sort().forEach(function(l) {
    const opt = document.createElement("option");
    opt.value = l;
    opt.textContent = l;
    if (l === atual) opt.selected = true;
    sel.appendChild(opt);
  });
}

function _isSmdSetor(setor) {
  return ["SMD", "SMT"].includes((setor || "").toUpperCase());
}

function onSetorModalChange(setor) {
  const sel    = document.getElementById("modalLinha");
  const opcoes = OPCOES_LINHA();
  const linhas = setor ? (opcoes[setor] || []) : [];

  sel.innerHTML = '<option value="">Selecione a linha</option>';
  linhas.slice().sort().forEach(function(l) {
    const opt = document.createElement("option");
    opt.value = l;
    opt.textContent = l;
    sel.appendChild(opt);
  });

  document.getElementById("rowModalFase").style.display = _isSmdSetor(setor) ? "" : "none";
  document.getElementById("modalSetup").value = calcularSetupSugerido(setor, "");
  buscarMeta();
}

function onLinhaModalChange() {
  const setor = document.getElementById("modalSetor").value;
  const linha = document.getElementById("modalLinha").value;
  document.getElementById("modalSetup").value = calcularSetupSugerido(setor, linha);
  buscarMeta();
  sugerirHoraInicio();
}

function sugerirHoraInicio() {
  const data  = (document.getElementById("modalData").value  || "").trim();
  const turno = (document.getElementById("modalTurno").value || "").trim();
  const linha = (document.getElementById("modalLinha").value || "").trim();
  const hint  = document.getElementById("modalHoraInicioHint");

  if (!data || !turno || !linha) {
    if (hint) hint.style.display = "none";
    return;
  }

  const rows = document.querySelectorAll("tr[data-plan-id]");
  let ultimoFim = null;
  rows.forEach(function(row) {
    if (row.dataset.data  !== data)  return;
    if (row.dataset.turno !== turno) return;
    if (row.dataset.linha !== linha) return;
    const fim = (row.dataset.horaFim || "").slice(0, 5);
    if (!fim) return;
    if (!ultimoFim || fim > ultimoFim) ultimoFim = fim;
  });

  const campo = document.getElementById("modalHoraInicio");
  if (ultimoFim) {
    campo.value = ultimoFim;
    if (hint) {
      hint.textContent   = "Início sugerido com base no último planejamento desta linha.";
      hint.style.display = "";
    }
  } else {
    if (hint) hint.style.display = "none";
  }
}

// ─── Seleção de OP no modal ───────────────────────────────────────────────────
function onOpChange(selectEl, modeloInputId, saldoId) {
  const ops    = OPS_JSON();
  const op     = ops.find(o => String(o.id) === selectEl.value);
  const modelo = document.getElementById(modeloInputId);
  const saldo  = document.getElementById(saldoId);

  if (op) {
    modelo.value = op.produto;
    saldo.textContent = "Saldo da OP: " + Number(op.saldo).toLocaleString("pt-BR");
    saldo.style.display = "";
    if (modeloInputId === "modalModelo") buscarMeta();
  } else {
    modelo.value = "";
    saldo.style.display = "none";
  }
}

// ─── Busca de meta hora ───────────────────────────────────────────────────────
let _metaTimer = null;

function agendarBuscarMeta() {
  clearTimeout(_metaTimer);
  _metaTimer = setTimeout(buscarMeta, 700);
}

function buscarMeta(manual) {
  const info = document.getElementById("modalMetaInfo");
  if (!info) return;

  const codigo = (document.getElementById("modalModelo").value || "").trim().toUpperCase();
  const setor  = (document.getElementById("modalSetor").value  || "").trim().toUpperCase();
  const linha  = (document.getElementById("modalLinha").value  || "").trim().toUpperCase();

  if (!codigo) {
    if (manual) {
      info.textContent   = "Informe o código do modelo para buscar a meta.";
      info.className     = "form-text text-muted";
      info.style.display = "";
    } else {
      info.style.display = "none";
    }
    return;
  }

  const faseEl = document.getElementById("modalFase");
  const fase   = (_isSmdSetor(setor) && faseEl) ? (faseEl.value || "") : "";

  console.log("[buscarMeta] params:", { codigo, setor, linha, fase, isSmd: _isSmdSetor(setor), faseElVisible: faseEl ? faseEl.closest("#rowModalFase")?.style.display : "n/a" });

  let url;
  try {
    url = URL_META() + "?codigo=" + encodeURIComponent(codigo)
        + "&setor=" + encodeURIComponent(setor)
        + "&linha=" + encodeURIComponent(linha)
        + (fase ? "&fase=" + encodeURIComponent(fase) : "");
  } catch (e) {
    console.error("[buscarMeta] erro ao construir URL:", e);
    info.textContent   = "Erro interno ao buscar meta.";
    info.className     = "form-text text-danger";
    info.style.display = "";
    return;
  }

  console.log("[buscarMeta] url:", url);

  info.textContent   = "Buscando…";
  info.className     = "form-text text-muted";
  info.style.display = "";

  fetch(url)
    .then(function(r) {
      console.log("[buscarMeta] http status:", r.status);
      return r.json();
    })
    .then(function(data) {
      console.log("[buscarMeta] resposta:", JSON.stringify(data));
      if (data.meta !== null && data.meta !== undefined) {
        document.getElementById("modalTaxa").value = Math.round(data.meta);
        info.textContent   = "Meta encontrada: " + Math.round(data.meta) + " pç/h";
        info.className     = "form-text text-success";
        info.style.display = "";
      } else {
        info.textContent   = "Modelo não cadastrado — informe a meta manualmente.";
        info.className     = "form-text text-warning";
        info.style.display = "";
      }
      if (data.setup_sugerido !== undefined && data.setup_sugerido > 0) {
        const setupEl = document.getElementById("modalSetup");
        if (!setupEl.value || setupEl.value === "0") {
          setupEl.value = data.setup_sugerido;
        }
      }
    })
    .catch(function(e) {
      console.error("[buscarMeta] fetch error:", e);
      info.textContent   = "Erro ao buscar meta.";
      info.className     = "form-text text-danger";
      info.style.display = "";
    });
}

// ─── Criar planejamento ───────────────────────────────────────────────────────
function salvarPlanejamento() {
  const payload = {
    data:                  document.getElementById("modalData").value,
    turno:                 document.getElementById("modalTurno").value,
    setor:                 document.getElementById("modalSetor").value,
    linha:                 document.getElementById("modalLinha").value,
    op_id:                 document.getElementById("modalOp").value || null,
    modelo:                document.getElementById("modalModelo").value,
    quantidade_planejada:  document.getElementById("modalQtd").value,
    taxa_horaria:          document.getElementById("modalTaxa").value || 0,
    setup_min:             document.getElementById("modalSetup").value || 0,
    hora_inicio_prevista:  document.getElementById("modalHoraInicio").value,
    observacao:            document.getElementById("modalObs").value,
  };

  fetch(URL_CRIAR(), {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(payload),
  })
  .then(r => r.json())
  .then(function(data) {
    if (data.ok) {
      const fim = data.hora_fim_prevista;
      const msg = fim
        ? "Planejamento criado. Fim previsto: " + fim
        : "Planejamento criado (sem meta/hora, fim não calculado).";
      bootstrap.Modal.getInstance(document.getElementById("modalNovo")).hide();
      mostrarAlerta("success", msg);
      setTimeout(() => location.reload(), 1000);
    } else {
      mostrarAlerta("danger", data.erro || "Erro ao criar.");
    }
  })
  .catch(() => mostrarAlerta("danger", "Erro de conexão."));
}

// ─── Editar planejamento ──────────────────────────────────────────────────────
function abrirEditar(id) {
  const row = document.querySelector(`[data-plan-id="${id}"]`);
  if (!row) return;

  document.getElementById("editId").value              = id;
  document.getElementById("editInfoLinha").textContent = row.dataset.linha;
  document.getElementById("editInfoTurno").textContent = row.dataset.turno;
  document.getElementById("editInfoData").textContent  = row.dataset.data;
  document.getElementById("editOp").value              = row.dataset.opId || "";
  document.getElementById("editModelo").value          = row.dataset.modelo;
  document.getElementById("editQtd").value             = row.dataset.qtd;
  document.getElementById("editTaxa").value            = row.dataset.taxa;
  document.getElementById("editSetup").value           = row.dataset.setup || 0;
  document.getElementById("editHoraInicio").value      = row.dataset.horaInicio;
  document.getElementById("editObs").value             = row.dataset.obs || "";
  document.getElementById("editSaldo").style.display   = "none";

  const ops = OPS_JSON();
  const op  = ops.find(o => String(o.id) === row.dataset.opId);
  if (op) {
    document.getElementById("editSaldo").textContent   = "Saldo da OP: " + Number(op.saldo).toLocaleString("pt-BR");
    document.getElementById("editSaldo").style.display = "";
  }

  new bootstrap.Modal(document.getElementById("modalEditar")).show();
}

function salvarEdicao() {
  const id = document.getElementById("editId").value;
  const payload = {
    op_id:                 document.getElementById("editOp").value || null,
    modelo:                document.getElementById("editModelo").value,
    quantidade_planejada:  document.getElementById("editQtd").value,
    taxa_horaria:          document.getElementById("editTaxa").value || 0,
    setup_min:             document.getElementById("editSetup").value || 0,
    hora_inicio_prevista:  document.getElementById("editHoraInicio").value,
    observacao:            document.getElementById("editObs").value,
  };

  const url = URL_EDITAR_TPL().replace("0", id);
  fetch(url, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(payload),
  })
  .then(r => r.json())
  .then(function(data) {
    if (data.ok) {
      bootstrap.Modal.getInstance(document.getElementById("modalEditar")).hide();
      mostrarAlerta("success", "Atualizado.");
      setTimeout(() => location.reload(), 800);
    } else {
      mostrarAlerta("danger", data.erro || "Erro ao atualizar.");
    }
  })
  .catch(() => mostrarAlerta("danger", "Erro de conexão."));
}

// ─── Atualizar status ─────────────────────────────────────────────────────────
function atualizarStatus(id, status) {
  const url = URL_STATUS_TPL().replace("0", id);
  fetch(url, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ status }),
  })
  .then(r => r.json())
  .then(function(data) {
    if (data.ok) {
      mostrarAlerta("success", "Status atualizado.");
      setTimeout(() => location.reload(), 600);
    } else {
      mostrarAlerta("danger", data.erro || "Erro.");
    }
  })
  .catch(() => mostrarAlerta("danger", "Erro de conexão."));
}

// ─── Excluir planejamento ─────────────────────────────────────────────────────
function excluirPlanejamento(id) {
  if (!confirm("Excluir este planejamento?")) return;
  const url = URL_EXCLUIR_TPL().replace("0", id);
  fetch(url, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
  })
  .then(r => r.json())
  .then(function(data) {
    if (data.ok) {
      mostrarAlerta("success", "Excluído.");
      setTimeout(() => location.reload(), 600);
    } else {
      mostrarAlerta("danger", data.erro || "Erro.");
    }
  })
  .catch(() => mostrarAlerta("danger", "Erro de conexão."));
}

// ─── Imprimir Resumo de Produção ──────────────────────────────────────────────
function imprimirResumo() {
  const data   = _root().dataset.dataSelecionada || "";
  const turno  = document.querySelector("select[name=turno]")?.value || "";
  const setor  = document.getElementById("resumo-setor-print")?.value || "";
  const base   = _root().dataset.urlResumoImprimir;

  let url = base + "?data=" + encodeURIComponent(data);
  if (turno) url += "&turno=" + encodeURIComponent(turno);
  if (setor) url += "&setor=" + encodeURIComponent(setor);

  window.open(url, "_blank");
}

// ─── Modal Novo: sugerir início ao abrir ─────────────────────────────────────
document.addEventListener("DOMContentLoaded", function() {
  const modalEl = document.getElementById("modalNovo");
  if (modalEl) {
    modalEl.addEventListener("show.bs.modal", function() {
      sugerirHoraInicio();
    });
  }
});

// ─── Alertas ──────────────────────────────────────────────────────────────────
function mostrarAlerta(tipo, msg) {
  const area = document.getElementById("alertArea");
  if (!area) return;
  const div = document.createElement("div");
  div.className = `alert alert-${tipo} alert-dismissible d-flex align-items-center gap-2 mb-3`;
  div.role = "alert";
  div.innerHTML = `<i class="bi bi-${tipo === "success" ? "check-circle-fill" : "x-circle-fill"} fs-5 flex-shrink-0"></i>
    <div>${msg}</div>
    <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>`;
  area.prepend(div);
  setTimeout(() => div.remove(), 5000);
}
