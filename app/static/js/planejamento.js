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

  let url;
  try {
    url = URL_META() + "?codigo=" + encodeURIComponent(codigo)
        + "&setor=" + encodeURIComponent(setor)
        + "&linha=" + encodeURIComponent(linha)
        + (fase ? "&fase=" + encodeURIComponent(fase) : "");
  } catch (e) {
    info.textContent   = "Erro interno ao buscar meta.";
    info.className     = "form-text text-danger";
    info.style.display = "";
    return;
  }

  info.textContent   = "Buscando…";
  info.className     = "form-text text-muted";
  info.style.display = "";

  fetch(url)
    .then(r => r.json())
    .then(function(data) {
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
    .catch(function() {
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

// ─── Plano de Voo (Gantt) ─────────────────────────────────────────────────────
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
        PLANEJADO:   "#0d6efd",
        EM_EXECUCAO: "#fd7e14",
        CONCLUIDO:   "#198754",
        CANCELADO:   "#6c757d",
      };

      const TURNO_RANGE = { start: 360, end: 1440 };

      function toMin(hhmm) {
        if (!hhmm) return null;
        const [h, m] = hhmm.split(":").map(Number);
        return h * 60 + m;
      }

      function pct(min) {
        return ((min - TURNO_RANGE.start) / (TURNO_RANGE.end - TURNO_RANGE.start) * 100).toFixed(2) + "%";
      }

      let html = '<div style="overflow-x:auto;">';
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

// ─── Detalhamento hora a hora ─────────────────────────────────────────────────
function gerarDetalhe() {
  var _dataInput = document.querySelector("input[name=data]");
  const data  = _root().dataset.dataSelecionada || (_dataInput ? _dataInput.value : "") || "";
  const turno = document.getElementById("detalhe-turno").value;
  const setor = document.getElementById("detalhe-setor").value;
  const linha = document.getElementById("detalhe-linha").value;
  const cont  = document.getElementById("detalheContainer");

  if (!turno || !linha) {
    cont.innerHTML = '<div class="alert alert-warning py-2 px-3 small" style="border-radius:8px;">Selecione turno e linha.</div>';
    return;
  }

  cont.innerHTML = '<div class="text-center text-muted py-3"><div class="spinner-border spinner-border-sm me-2"></div>Calculando...</div>';

  const url = URL_DETALHE()
    + "?data="  + encodeURIComponent(data)
    + "&turno=" + encodeURIComponent(turno)
    + "&setor=" + encodeURIComponent(setor)
    + "&linha=" + encodeURIComponent(linha);

  fetch(url)
    .then(r => r.json())
    .then(function(resp) {
      if (resp.erro) {
        cont.innerHTML = '<div class="alert alert-danger py-2 px-3 small" style="border-radius:8px;">' + resp.erro + '</div>';
        return;
      }

      const slots = resp.slots || [];
      if (!slots.length) {
        cont.innerHTML = '<div class="p-3 text-center text-muted small">Nenhum planejamento encontrado para esta linha/turno/data.</div>';
        return;
      }

      const TIPO_LABEL = {
        INTERVALO_1: "Intervalo 1", INTERVALO_2: "Intervalo 2",
        GINASTICA: "Ginástica", DDS: "DDS", REFEICAO: "Refeição",
        SETUP: "Setup", OUTROS: "Outros", PARADA: "Parada",
      };

      let html = '<div class="table-responsive"><table class="table table-sm table-hover mb-0" style="font-size:0.82rem;">';
      html += `<thead style="font-size:0.72rem;text-transform:uppercase;letter-spacing:.4px;background:var(--bg);">
        <tr>
          <th class="ps-3 py-2">Hora</th>
          <th>Modelo</th>
          <th class="text-center">Setup</th>
          <th class="text-center">Paradas</th>
          <th class="text-center">Produção</th>
          <th class="text-end">Peças/hora</th>
          <th class="text-end pe-3">Total acum.</th>
        </tr>
      </thead><tbody>`;

      let lastModelo = null;
      slots.forEach(function(s) {
        const isNewModelo = s.modelo !== lastModelo;
        if (isNewModelo && lastModelo !== null) {
          html += `<tr style="border-top:2px solid var(--border);">
            <td colspan="7" class="px-3 py-1" style="background:var(--bg);font-size:0.73rem;color:var(--text-muted);">
              <i class="bi bi-arrow-right-circle me-1"></i>Início: ${s.modelo}
            </td>
          </tr>`;
        }
        lastModelo = s.modelo;

        const paradasDesc = s.paradas && s.paradas.length
          ? s.paradas.map(p => (TIPO_LABEL[p.tipo] || p.tipo) + " " + p.duracao + "min").join(", ")
          : "—";

        const rowStyle = s.concluiu ? 'style="background:#f0fdf4;"' : "";

        html += `<tr ${rowStyle}>
          <td class="ps-3 fw-semibold text-nowrap">${s.hora_inicio} – ${s.hora_fim}</td>
          <td class="text-nowrap">${s.modelo}${s.op_numero ? ' <span class="text-muted small">· ' + s.op_numero + '</span>' : ''}</td>
          <td class="text-center">
            ${s.setup_min > 0
              ? '<span class="badge bg-warning text-dark" style="font-size:0.68rem;">' + s.setup_min + ' min</span>'
              : '<span class="text-muted">—</span>'}
          </td>
          <td class="text-center" style="font-size:0.78rem;">
            ${s.paradas_min > 0
              ? '<span class="text-danger">' + paradasDesc + '</span>'
              : '<span class="text-muted">—</span>'}
          </td>
          <td class="text-center">
            <span class="fw-semibold">${s.producao_min} min</span>
          </td>
          <td class="text-end fw-semibold">
            ${s.pecas > 0 ? s.pecas.toLocaleString("pt-BR") : '<span class="text-muted">0</span>'}
          </td>
          <td class="text-end pe-3 fw-bold ${s.concluiu ? 'text-success' : ''}">
            ${s.total_acumulado.toLocaleString("pt-BR")}
            ${s.concluiu ? ' <i class="bi bi-check-circle-fill text-success" style="font-size:0.75rem;"></i>' : ''}
          </td>
        </tr>`;
      });

      html += '</tbody></table></div>';
      cont.innerHTML = html;
    })
    .catch(function() {
      cont.innerHTML = '<div class="alert alert-danger py-2 px-3 small" style="border-radius:8px;">Erro de conexão.</div>';
    });
}

// ─── Imprimir Plano de Voo ─────────────────────────────────────────────────────
function imprimirPlanoVoo() {
  var _dataInput = document.querySelector("input[name=data]");
  const data  = _root().dataset.dataSelecionada || (_dataInput ? _dataInput.value : "") || "";
  const turno = document.getElementById("detalhe-turno").value;
  const setor = document.getElementById("detalhe-setor").value;
  const linha = document.getElementById("detalhe-linha").value;

  if (!turno || !linha) {
    alert("Selecione turno e linha antes de imprimir.");
    return;
  }

  const url = _root().dataset.urlImprimir
    + "?data="  + encodeURIComponent(data)
    + "&turno=" + encodeURIComponent(turno)
    + "&setor=" + encodeURIComponent(setor)
    + "&linha=" + encodeURIComponent(linha);

  window.open(url, "_blank");
}

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
