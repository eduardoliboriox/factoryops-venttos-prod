"use strict";

// URLs injetadas pelo template via atributos data no elemento #planejamento-root
const _root        = () => document.getElementById("planejamento-root");
const URL_CRIAR_LOTE  = () => _root().dataset.urlCriarLote;
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

// ─── Filtro dinâmico de linhas (fora do modal) ────────────────────────────────
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

// ─── Modal Novo: setor muda → atualiza linhas + todos os cards ────────────────
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

  document.querySelectorAll("#modelosList .modelo-card").forEach(function(card) {
    card.querySelector(".row-fase").style.display = _isSmdSetor(setor) ? "" : "none";
    card.querySelector(".model-setup").value = calcularSetupSugerido(setor, "");
  });
}

// ─── Modal Novo: linha muda → atualiza setup de todos os cards ───────────────
function onLinhaModalChange() {
  const setor = document.getElementById("modalSetor").value;
  const linha = document.getElementById("modalLinha").value;

  document.querySelectorAll("#modelosList .modelo-card").forEach(function(card) {
    card.querySelector(".model-setup").value = calcularSetupSugerido(setor, linha);
  });

  sugerirHoraInicio();
}

// ─── Sugestão de hora de início ───────────────────────────────────────────────
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

// ─── Seleção de OP no modal de edição ────────────────────────────────────────
function onOpChange(selectEl, modeloInputId, saldoId) {
  const ops    = OPS_JSON();
  const op     = ops.find(o => String(o.id) === selectEl.value);
  const modelo = document.getElementById(modeloInputId);
  const saldo  = document.getElementById(saldoId);

  if (op) {
    modelo.value = op.produto;
    saldo.textContent = "Saldo da OP: " + Number(op.saldo).toLocaleString("pt-BR");
    saldo.style.display = "";
  } else {
    modelo.value = "";
    saldo.style.display = "none";
  }
}

// ─── Multi-modelo: gerenciamento de cards ────────────────────────────────────
let _cardMetaTimer = null;

function _popularOpSelect(selectEl) {
  const ops = OPS_JSON();
  selectEl.innerHTML = '<option value="">— Nenhuma OP —</option>';
  ops.forEach(function(op) {
    const opt = document.createElement("option");
    opt.value = op.id;
    opt.textContent = op.numero_op + " · " + op.produto + " · Saldo: " + Number(op.saldo).toLocaleString("pt-BR");
    selectEl.appendChild(opt);
  });
}

function adicionarModelo() {
  const list  = document.getElementById("modelosList");
  const tpl   = document.getElementById("modeloCardTemplate");
  const clone = tpl.content.cloneNode(true);
  const card  = clone.querySelector(".modelo-card");
  const index = list.children.length;

  card.dataset.modelIndex = index;
  card.querySelector(".modelo-numero").textContent = "Modelo " + (index + 1);

  _popularOpSelect(card.querySelector(".model-op"));

  const setor = document.getElementById("modalSetor").value;
  const linha = document.getElementById("modalLinha").value;

  if (_isSmdSetor(setor)) {
    card.querySelector(".row-fase").style.display = "";

    // Herda a fase do último card existente (evita buscar com fase errada)
    const cards = list.querySelectorAll(".modelo-card");
    if (cards.length > 0) {
      const lastFase = cards[cards.length - 1].querySelector(".model-fase");
      if (lastFase) {
        card.querySelector(".model-fase").value = lastFase.value;
      }
    }
  }
  card.querySelector(".model-setup").value = calcularSetupSugerido(setor, linha);

  list.appendChild(clone);
  _updateRemoverButtons();
}

function removerModelo(btn) {
  const list = document.getElementById("modelosList");
  if (list.children.length <= 1) return;
  btn.closest(".modelo-card").remove();
  _renumerarModelos();
  _updateRemoverButtons();
}

function _renumerarModelos() {
  document.querySelectorAll("#modelosList .modelo-card").forEach(function(card, i) {
    card.dataset.modelIndex = i;
    card.querySelector(".modelo-numero").textContent = "Modelo " + (i + 1);
  });
}

function _updateRemoverButtons() {
  const cards = document.querySelectorAll("#modelosList .modelo-card");
  cards.forEach(function(card) {
    const btn = card.querySelector(".btn-remover-modelo");
    if (btn) btn.style.visibility = cards.length > 1 ? "visible" : "hidden";
  });
}

function toggleAteFim(checkbox) {
  const qtdInput = checkbox.closest(".modelo-card").querySelector(".model-qtd");
  qtdInput.disabled = checkbox.checked;
  if (checkbox.checked) {
    qtdInput.value = "";
    qtdInput.placeholder = "Até o fim do turno";
  } else {
    qtdInput.placeholder = "";
    qtdInput.disabled = false;
  }
}

// ─── OP por card ──────────────────────────────────────────────────────────────
function onOpChangeCard(selectEl) {
  const card   = selectEl.closest(".modelo-card");
  const ops    = OPS_JSON();
  const op     = ops.find(function(o) { return String(o.id) === selectEl.value; });
  const modelo = card.querySelector(".model-codigo");
  const saldo  = card.querySelector(".model-saldo");

  if (op) {
    modelo.value = op.produto;
    saldo.textContent = "Saldo da OP: " + Number(op.saldo).toLocaleString("pt-BR");
    saldo.style.display = "";
    buscarMetaCard(card, false, true);
  } else {
    modelo.value = "";
    saldo.style.display = "none";
  }
}

// ─── Busca de meta por card ───────────────────────────────────────────────────
function agendarBuscarMetaCard(card) {
  clearTimeout(_cardMetaTimer);
  _cardMetaTimer = setTimeout(function() { buscarMetaCard(card); }, 700);
}

function buscarMetaCard(card, manual, fromOpSelect) {
  const info   = card.querySelector(".model-meta-info");
  const codigo = (card.querySelector(".model-codigo").value || "").trim().toUpperCase();
  const setor  = (document.getElementById("modalSetor").value || "").trim().toUpperCase();
  const linha  = (document.getElementById("modalLinha").value || "").trim().toUpperCase();
  const faseEl = card.querySelector(".model-fase");
  const fase   = (!fromOpSelect && _isSmdSetor(setor) && faseEl) ? (faseEl.value || "") : "";

  if (!codigo) {
    if (manual) {
      info.textContent   = "Informe o código do modelo para buscar a meta.";
      info.className     = "model-meta-info form-text text-muted";
      info.style.display = "";
    } else {
      info.style.display = "none";
    }
    return;
  }

  let url;
  try {
    url = URL_META() + "?codigo=" + encodeURIComponent(codigo)
        + "&setor=" + encodeURIComponent(setor)
        + "&linha=" + encodeURIComponent(linha)
        + (fase ? "&fase=" + encodeURIComponent(fase) : "");
  } catch (e) {
    return;
  }

  info.textContent   = "Buscando…";
  info.className     = "model-meta-info form-text text-muted";
  info.style.display = "";

  fetch(url)
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.meta !== null && data.meta !== undefined) {
        card.querySelector(".model-taxa").value = Math.round(data.meta);
        info.textContent   = "Meta encontrada: " + Math.round(data.meta) + " pç/h";
        info.className     = "model-meta-info form-text text-success";
        info.style.display = "";
        if (data.fase_encontrada && faseEl && fromOpSelect) {
          faseEl.value = data.fase_encontrada;
        }
      } else {
        info.textContent   = "Modelo não cadastrado — informe a meta manualmente.";
        info.className     = "model-meta-info form-text text-warning";
        info.style.display = "";
      }
      if (data.setup_sugerido && data.setup_sugerido > 0) {
        const setupEl = card.querySelector(".model-setup");
        if (!setupEl.value || setupEl.value === "0") {
          setupEl.value = data.setup_sugerido;
        }
      }
    })
    .catch(function() {
      info.textContent   = "Erro ao buscar meta.";
      info.className     = "model-meta-info form-text text-danger";
      info.style.display = "";
    });
}

// ─── Criar planejamento (lote) ────────────────────────────────────────────────
function salvarPlanejamento() {
  const cards   = document.querySelectorAll("#modelosList .modelo-card");
  const modelos = [];

  for (const card of cards) {
    const ateFim = card.querySelector(".model-ate-fim").checked;
    const qtdRaw = card.querySelector(".model-qtd").value;
    const qtd    = ateFim ? 0 : (parseInt(qtdRaw) || 0);

    modelos.push({
      op_id:                (card.querySelector(".model-op").value || null),
      modelo:               (card.querySelector(".model-codigo").value || "").trim(),
      quantidade_planejada: qtd,
      taxa_horaria:         parseInt(card.querySelector(".model-taxa").value)  || 0,
      setup_min:            parseInt(card.querySelector(".model-setup").value) || 0,
      observacao:           (card.querySelector(".model-obs").value || "").trim() || null,
    });
  }

  const payload = {
    header: {
      data:                 document.getElementById("modalData").value,
      turno:                document.getElementById("modalTurno").value,
      setor:                document.getElementById("modalSetor").value,
      linha:                document.getElementById("modalLinha").value,
      hora_inicio_prevista: document.getElementById("modalHoraInicio").value,
    },
    modelos,
  };

  fetch(URL_CRIAR_LOTE(), {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(payload),
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.ok) {
      bootstrap.Modal.getInstance(document.getElementById("modalNovo")).hide();
      const n = modelos.length;
      mostrarAlerta("success", n === 1 ? "Planejamento criado." : n + " modelos planejados.");
      setTimeout(function() { location.reload(); }, 1000);
    } else {
      mostrarAlerta("danger", data.erro || "Erro ao criar.");
    }
  })
  .catch(function() { mostrarAlerta("danger", "Erro de conexão."); });
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

// ─── Inicialização do modal ───────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", function() {
  const modalEl = document.getElementById("modalNovo");
  if (modalEl) {
    modalEl.addEventListener("show.bs.modal", function() {
      const list = document.getElementById("modelosList");
      if (list && list.children.length === 0) {
        adicionarModelo();
      }
      sugerirHoraInicio();
    });

    modalEl.addEventListener("hidden.bs.modal", function() {
      const list = document.getElementById("modelosList");
      if (list) list.innerHTML = "";
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
