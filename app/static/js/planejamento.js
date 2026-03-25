"use strict";

// URLs injetadas pelo template via atributos data no elemento #planejamento-root
const _root = () => document.getElementById("planejamento-root");
const URL_CRIAR      = () => _root().dataset.urlCriar;
const URL_PLANO      = () => _root().dataset.urlPlano;
const URL_EDITAR_TPL = () => _root().dataset.urlEditarTpl;
const URL_STATUS_TPL = () => _root().dataset.urlStatusTpl;
const URL_EXCLUIR_TPL= () => _root().dataset.urlExcluirTpl;

const OPS_JSON = () => JSON.parse(_root().dataset.ops || "[]");
const OPCOES_LINHA = () => JSON.parse(_root().dataset.opcoes || "{}");

// ─── Filtro dinâmico de linhas ─────────────────────────────────────────────
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

function onSetorModalChange(setor) {
  onSetorChange(setor, "modalLinha");
}

// ─── Seleção de OP no modal ───────────────────────────────────────────────
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

// ─── Criar planejamento ───────────────────────────────────────────────────
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
        : "Planejamento criado (sem taxa horária, fim não calculado).";
      bootstrap.Modal.getInstance(document.getElementById("modalNovo")).hide();
      mostrarAlerta("success", msg);
      setTimeout(() => location.reload(), 1000);
    } else {
      mostrarAlerta("danger", data.erro || "Erro ao criar.");
    }
  })
  .catch(() => mostrarAlerta("danger", "Erro de conexão."));
}

// ─── Editar planejamento ──────────────────────────────────────────────────
function abrirEditar(id) {
  const row = document.querySelector(`[data-plan-id="${id}"]`);
  if (!row) return;

  document.getElementById("editId").value                 = id;
  document.getElementById("editInfoLinha").textContent    = row.dataset.linha;
  document.getElementById("editInfoTurno").textContent    = row.dataset.turno;
  document.getElementById("editInfoData").textContent     = row.dataset.data;
  document.getElementById("editOp").value                 = row.dataset.opId || "";
  document.getElementById("editModelo").value             = row.dataset.modelo;
  document.getElementById("editQtd").value                = row.dataset.qtd;
  document.getElementById("editTaxa").value               = row.dataset.taxa;
  document.getElementById("editHoraInicio").value         = row.dataset.horaInicio;
  document.getElementById("editObs").value                = row.dataset.obs || "";
  document.getElementById("editSaldo").style.display      = "none";

  const ops = OPS_JSON();
  const op  = ops.find(o => String(o.id) === row.dataset.opId);
  if (op) {
    document.getElementById("editSaldo").textContent = "Saldo da OP: " + Number(op.saldo).toLocaleString("pt-BR");
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

// ─── Atualizar status ─────────────────────────────────────────────────────
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

// ─── Excluir planejamento ─────────────────────────────────────────────────
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

// ─── Plano de Voo ─────────────────────────────────────────────────────────
function renderPlanoDeVoo(data) {
  const container = document.getElementById("planoDeVooContainer");
  if (!container) return;

  container.innerHTML = '<div class="text-center text-muted py-4"><div class="spinner-border spinner-border-sm me-2"></div>Carregando...</div>';

  fetch(URL_PLANO() + "?data=" + data)
    .then(r => r.json())
    .then(function(agrupado) {
      if (agrupado.erro) {
        container.innerHTML = '<div class="alert alert-warning">' + agrupado.erro + '</div>';
        return;
      }

      const linhas = Object.keys(agrupado).sort();
      if (!linhas.length) {
        container.innerHTML = '<div class="p-4 text-center text-muted small"><i class="bi bi-calendar-x d-block fs-2 mb-2 opacity-25"></i>Nenhum planejamento para esta data.</div>';
        return;
      }

      const STATUS_CORES = {
        PLANEJADO:    "#0d6efd",
        EM_EXECUCAO:  "#fd7e14",
        CONCLUIDO:    "#198754",
        CANCELADO:    "#6c757d",
      };

      const TURNO_RANGE = { start: 360, end: 1440 }; // 06:00 a 24:00 em minutos

      function toMin(hhmm) {
        if (!hhmm) return null;
        const [h, m] = hhmm.split(":").map(Number);
        return h * 60 + m;
      }

      function pct(min) {
        return ((min - TURNO_RANGE.start) / (TURNO_RANGE.end - TURNO_RANGE.start) * 100).toFixed(2) + "%";
      }

      let html = '<div style="overflow-x:auto;">';

      // cabeçalho de horas
      html += '<div style="display:flex;margin-left:100px;margin-bottom:4px;">';
      for (let h = 6; h <= 23; h++) {
        html += `<div style="flex:1;font-size:0.68rem;color:#94a3b8;text-align:center;">${String(h).padStart(2,"0")}h</div>`;
      }
      html += "</div>";

      linhas.forEach(function(linha) {
        const itens = agrupado[linha];
        html += `<div style="display:flex;align-items:center;margin-bottom:6px;">`;
        html += `<div style="width:100px;font-size:0.78rem;font-weight:600;color:#1e293b;flex-shrink:0;padding-right:8px;text-align:right;">${linha}</div>`;
        html += `<div style="flex:1;height:32px;background:#f1f5f9;border-radius:6px;position:relative;overflow:hidden;">`;

        itens.forEach(function(item) {
          const s = toMin(item.hora_inicio_prevista);
          const e = toMin(item.hora_fim_prevista);
          if (s === null) return;

          const left  = pct(Math.max(s, TURNO_RANGE.start));
          const width = e ? pct(Math.min(e, TURNO_RANGE.end) - Math.max(s, TURNO_RANGE.start)) : "30px";
          const cor   = STATUS_CORES[item.status] || "#0d6efd";
          const borda = e ? "none" : `2px dashed ${cor}`;

          html += `<div title="${item.modelo} · ${item.quantidade_planejada} pç"
            style="position:absolute;left:${left};width:${width};height:100%;
                   background:${e ? cor : "transparent"};
                   border:${borda};
                   border-radius:4px;
                   display:flex;align-items:center;padding:0 6px;
                   font-size:0.68rem;color:${e ? "#fff" : cor};
                   white-space:nowrap;overflow:hidden;cursor:default;">
            ${item.modelo}${!e ? " ?" : ""}
          </div>`;
        });

        html += "</div></div>";
      });

      html += "</div>";
      container.innerHTML = html;
    })
    .catch(() => {
      container.innerHTML = '<div class="alert alert-warning">Erro ao carregar plano de voo.</div>';
    });
}

// ─── Alertas ──────────────────────────────────────────────────────────────
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
