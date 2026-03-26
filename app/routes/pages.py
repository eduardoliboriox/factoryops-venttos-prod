from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.auth.decorators import admin_required
from app.services import time_studies_service


bp = Blueprint("pages", __name__)


@bp.route("/")
@login_required
def inicio():
    return render_template("inicio.html", active_menu="inicio")


@bp.route("/dashboard")
@login_required
def dashboard():
    filtros = {
        "data_inicial": "",
        "data_final": "",
        "turno": "",
        "filial": "",
    }

    kpis = {
        "absenteismo": 0,
        "linhas": 0,
    }

    return render_template(
        "dashboard.html",
        active_menu="dashboard",
        filtros=filtros,
        kpis=kpis,
        ranking_extras=[],
        ranking_objetivos=[],
        ranking_clientes=[],
        ranking_tipos_provisao=[],
    )


@bp.route("/powerbi")
@login_required
def powerbi():
    return render_template("powerbi.html", active_menu="powerbi")


@bp.route("/smt")
@login_required
def smt_home():
    return render_template("inicio.html", active_menu="inicio")


@bp.route("/smt/dashboard")
@login_required
def smt_dashboard():
    return render_template("inicio.html", active_menu="inicio")


@bp.route("/smt/modelos")
@login_required
def smt_modelos():
    return render_template("funcionalidades/modelos_smt.html", active_menu="smt_modelos")


@bp.route("/smt/cadastro")
@login_required
def smt_cadastro():
    return render_template("funcionalidades/cadastro.html", active_menu="smt_cadastro")


@bp.route("/smt/calcular")
@login_required
def smt_calcular():
    return render_template("funcionalidades/calcular.html", active_menu="smt_calcular")


@bp.route("/smt/estudo-tempo")
@login_required
def smt_estudo_tempo():
    return render_template("engenharia/estudo_tempo.html", active_menu="smt_estudo_tempo")


@bp.route("/smt/mais")
@login_required
def smt_mais():
    return render_template("mais.html", active_menu="smt_more")


@bp.route("/smt/estudo-tempo/print/<int:study_id>")
@login_required
def smt_estudo_tempo_print(study_id: int):
    detail = time_studies_service.get_study_detail(study_id)
    if not detail:
        return render_template(
            "engenharia/estudo_tempo_print.html",
            active_menu="smt_estudo_tempo",
            study=None,
            operations=[],
            totals={},
            not_found=True,
        )

    return render_template(
        "engenharia/estudo_tempo_print.html",
        active_menu="smt_estudo_tempo",
        study=detail.get("study"),
        operations=detail.get("operations") or [],
        totals=detail.get("totals") or {},
        not_found=False,
    )


# ─── Funcionalidades ────────────────────────────────────────────────────────

@bp.route("/funcionalidades/im-pa")
@login_required
def funcionalidades_im_pa():
    return render_template("funcionalidades/im_pa.html", active_menu="funcionalidades_im_pa")


@bp.route("/funcionalidades/pth")
@login_required
def funcionalidades_pth():
    return render_template("funcionalidades/pth.html", active_menu="funcionalidades_pth")


@bp.route("/funcionalidades/vtt")
@login_required
def funcionalidades_vtt():
    return render_template("funcionalidades/vtt.html", active_menu="funcionalidades_vtt")


# ─── Produção ────────────────────────────────────────────────────────────────

@bp.route("/producao/medicao-pasta-solda")
@login_required
def producao_medicao_pasta():
    return render_template("producao/medicao_pasta_solda.html", active_menu="producao_medicao_pasta")


@bp.route("/producao/checklist-verificacao-linha")
@login_required
def producao_checklist_linha():
    return render_template("producao/checklist_linha.html", active_menu="producao_checklist_linha")


@bp.route("/producao/checklist-verificacao-linha/<int:sessao_id>")
@login_required
def producao_checklist_detalhe(sessao_id: int):
    from app.services import checklist_service
    sessao = checklist_service.get_sessao_detail(sessao_id)
    return render_template(
        "producao/checklist_detalhe.html",
        active_menu="producao_checklist_linha",
        sessao=sessao,
    )


@bp.route("/producao/limpeza-stencil")
@login_required
def producao_limpeza_stencil():
    return render_template("producao/limpeza_stencil.html", active_menu="producao_limpeza_stencil")


# ─── Engenharia ──────────────────────────────────────────────────────────────

@bp.route("/engenharia/folha-cronometragem")
@login_required
def engenharia_folha_crono():
    return render_template("engenharia/folha_cronometragem.html", active_menu="engenharia_folha_crono")


# ─── PCP ─────────────────────────────────────────────────────────────────────

@bp.route("/pcp/producao-coletada")
@login_required
@admin_required
def pcp_producao_coletada():
    from flask import request
    from app.services import producao_coletada_service as svc

    data_inicial_pad, data_final_pad = svc.data_padrao()

    data_inicial = request.args.get("dataInicial", data_inicial_pad)
    data_final   = request.args.get("dataFinal",   data_final_pad)
    setor        = request.args.get("setor",  "")
    linha        = request.args.get("linha",  "")
    turno        = request.args.get("turno",  "")

    try:
        registros = svc.listar(data_inicial, data_final, setor, linha, turno)
        kpis      = svc.totais(data_inicial, data_final, setor, linha, turno)
        filtros   = svc.filtros_disponiveis(setor)
        erro      = None
    except Exception as e:
        registros = []
        kpis      = {}
        filtros   = {"setores": [], "linhas": []}
        erro      = str(e)

    return render_template(
        "pcp/producao_coletada.html",
        active_menu="pcp_producao_coletada",
        data_inicial=data_inicial,
        data_final=data_final,
        setor=setor,
        linha=linha,
        turno=turno,
        registros=registros,
        kpis=kpis,
        filtros=filtros,
        erro=erro,
    )


@bp.route("/pcp/producao-coletada/importar", methods=["POST"])
@login_required
@admin_required
def pcp_producao_coletada_importar():
    from flask import request, jsonify
    from app.services import producao_coletada_service as svc

    arquivo = request.files.get("arquivo_json")
    if not arquivo or not arquivo.filename:
        return jsonify({"erro": "Nenhum arquivo enviado."}), 400

    if not arquivo.filename.endswith(".json"):
        return jsonify({"erro": "Somente arquivos .json são aceitos."}), 400

    try:
        job_id = svc.iniciar_importacao(arquivo.read())
        return jsonify({"job_id": job_id})
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception:
        return jsonify({"erro": "Erro inesperado ao processar o arquivo."}), 500


@bp.route("/pcp/producao-coletada/importar/progresso/<job_id>")
@login_required
@admin_required
def pcp_producao_coletada_progresso(job_id):
    from flask import jsonify
    from app.services import producao_coletada_service as svc

    return jsonify(svc.status_importacao(job_id))


# ─── CONFIGURAÇÕES DO SISTEMA ────────────────────────────────────────────────

@bp.route("/pcp/turnos")
@login_required
@admin_required
def pcp_turnos():
    from flask import redirect, url_for
    return redirect(url_for("pages.config_turnos"))


@bp.route("/config/turnos", methods=["GET", "POST"])
@login_required
@admin_required
def config_turnos():
    from flask import request, flash, redirect, url_for
    from app.services import turno_config_service as svc

    erro   = None
    turnos = {}

    if request.method == "POST":
        acao = request.form.get("acao")
        if acao == "adicionar":
            try:
                svc.adicionar(
                    request.form.get("turno", ""),
                    request.form.get("hora_inicio", ""),
                    request.form.get("hora_fim", ""),
                )
                flash("Intervalo adicionado.", "success")
            except ValueError as e:
                flash(str(e), "danger")
            except Exception as e:
                flash(str(e), "danger")
        elif acao == "excluir":
            try:
                svc.excluir(int(request.form.get("id")))
                flash("Intervalo removido.", "success")
            except Exception as e:
                flash(str(e), "danger")
        return redirect(url_for("pages.config_turnos"))

    try:
        turnos = svc.listar_por_turno()
    except Exception as e:
        erro = str(e)

    return render_template(
        "config/turnos.html",
        active_menu="config_turnos",
        turnos=turnos,
        erro=erro,
    )


@bp.route("/config/linhas")
@login_required
@admin_required
def config_linhas():
    from app.services import linha_config_service as svc

    erro   = None
    setores = {}
    linhas  = []

    try:
        setores = svc.listar_por_setor()
        linhas  = svc.listar_linhas_producao()
    except Exception as e:
        erro = str(e)

    return render_template(
        "config/linhas.html",
        active_menu="config_linhas",
        setores=setores,
        linhas=linhas,
        erro=erro,
    )


@bp.route("/config/linhas/atribuir", methods=["POST"])
@login_required
@admin_required
def config_linhas_atribuir():
    from flask import request, jsonify
    from app.services import linha_config_service as svc

    data  = request.get_json(silent=True) or {}
    setor = data.get("setor", "")
    linha = data.get("linha", "")

    try:
        svc.atribuir(setor, linha)
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@bp.route("/config/linhas/remover", methods=["POST"])
@login_required
@admin_required
def config_linhas_remover():
    from flask import request, jsonify
    from app.services import linha_config_service as svc

    data = request.get_json(silent=True) or {}
    try:
        svc.remover(int(data.get("id")))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@bp.route("/config/paradas", methods=["GET", "POST"])
@login_required
@admin_required
def config_paradas():
    from flask import request, flash, redirect, url_for
    from app.services import parada_config_service as svc

    erro    = None
    paradas = {}
    opcoes  = {}

    if request.method == "POST":
        acao = request.form.get("acao")
        if acao == "adicionar":
            try:
                svc.adicionar(request.form)
                flash("Parada adicionada.", "success")
            except ValueError as e:
                flash(str(e), "danger")
            except Exception as e:
                flash(str(e), "danger")
        elif acao == "excluir":
            try:
                svc.excluir(int(request.form.get("id")))
                flash("Parada removida.", "success")
            except Exception as e:
                flash(str(e), "danger")
        return redirect(url_for("pages.config_paradas"))

    try:
        paradas = svc.listar_por_setor()
        opcoes  = svc.opcoes_linha()
    except Exception as e:
        erro = str(e)

    return render_template(
        "config/paradas.html",
        active_menu="config_paradas",
        paradas=paradas,
        opcoes=opcoes,
        tipos=["INTERVALO_1", "INTERVALO_2", "GINASTICA", "DDS", "REFEICAO", "SETUP", "OUTROS"],
        erro=erro,
    )


# ─── PCP ─────────────────────────────────────────────────────────────────────

@bp.route("/pcp/controle-ops", methods=["GET", "POST"])
@login_required
def pcp_controle_ops():
    from flask import request, flash, redirect, url_for
    from app.services import controle_ops_service as svc

    erro    = None
    ops     = []
    filiais = []
    filial  = request.args.get("filial", "")
    status  = request.args.get("status", "")
    setor   = request.args.get("setor",  "")

    if request.method == "POST":
        try:
            svc.cadastrar(request.form)
            roteiro = request.form.get("roteiro_padrao") == "1"
            flash("Roteiro criado: 3 OPs cadastradas (PTH, IM, SMD)." if roteiro else "OP cadastrada com sucesso.", "success")
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Erro ao cadastrar. Verifique se a tabela foi criada.", "danger")
        return redirect(url_for("pages.pcp_controle_ops"))

    try:
        ops     = svc.listar(filial, status, setor)
        filiais = svc.filiais_disponiveis()
    except Exception as e:
        erro = str(e)

    return render_template(
        "pcp/controle_ops.html",
        active_menu="pcp_controle_ops",
        ops=ops,
        filiais=filiais,
        filial=filial,
        status=status,
        setor=setor,
        erro=erro,
    )


@bp.route("/pcp/controle-ops/<int:op_id>/editar", methods=["POST"])
@login_required
def pcp_controle_ops_editar(op_id):
    from flask import request, flash, redirect, url_for
    from app.services import controle_ops_service as svc

    try:
        svc.atualizar(op_id, request.form)
        flash("OP atualizada com sucesso.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Erro ao atualizar a OP.", "danger")
    return redirect(url_for("pages.pcp_controle_ops"))


@bp.route("/pcp/controle-ops/<int:op_id>/excluir", methods=["POST"])
@login_required
def pcp_controle_ops_excluir(op_id):
    from flask import flash, redirect, url_for
    from app.services import controle_ops_service as svc

    try:
        svc.excluir(op_id)
        flash("OP excluída.", "success")
    except Exception:
        flash("Erro ao excluir a OP.", "danger")
    return redirect(url_for("pages.pcp_controle_ops"))


@bp.route("/pcp/apontamento")
@login_required
def pcp_apontamento():
    from flask import request
    from app.services import apontamento_service as svc
    from app.services import producao_coletada_service as pc_svc

    data_inicial_pad, data_final_pad = svc.data_padrao()
    data_inicial = request.args.get("dataInicial", data_inicial_pad)
    data_final   = request.args.get("dataFinal",   data_final_pad)
    setor        = request.args.get("setor",  "")
    linha        = request.args.get("linha",  "")
    turno        = request.args.get("turno",  "")

    try:
        apontamentos = svc.listar_agrupado(data_inicial, data_final, setor, linha, turno)
        ops          = svc.ops_abertas("")
        filtros      = pc_svc.filtros_disponiveis(setor)
        erro         = None
    except Exception as e:
        apontamentos = []
        ops          = []
        filtros      = {"setores": [], "linhas": []}
        erro         = str(e)

    return render_template(
        "pcp/apontamento.html",
        active_menu="pcp_apontamento",
        data_inicial=data_inicial,
        data_final=data_final,
        setor=setor,
        linha=linha,
        turno=turno,
        apontamentos=apontamentos,
        ops=ops,
        filtros=filtros,
        erro=erro,
    )


@bp.route("/pcp/apontamento/vincular", methods=["POST"])
@login_required
def pcp_apontamento_vincular():
    from flask import request, jsonify
    from app.services import apontamento_service as svc

    data = request.get_json(silent=True) or {}
    try:
        svc.vincular(
            data.get("data", ""),
            data.get("turno", ""),
            data.get("modelo", ""),
            data.get("linha", ""),
            int(data.get("op_id", 0)),
            int(data.get("quantidade", 0)),
            setor=data.get("setor", ""),
            fase=data.get("fase") or None,
            lote=data.get("lote") or None,
        )
        return jsonify({"ok": True})
    except (ValueError, Exception) as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/pcp/apontamento/desvincular", methods=["POST"])
@login_required
def pcp_apontamento_desvincular():
    from flask import request, jsonify
    from app.services import apontamento_service as svc

    data = request.get_json(silent=True) or {}
    try:
        svc.desvincular(int(data.get("apontamento_id", 0)))
        return jsonify({"ok": True})
    except (ValueError, Exception) as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/pcp/planejamento")
@login_required
def pcp_planejamento():
    from flask import request
    from app.services import planejamento_service as svc
    from app.services import producao_coletada_service as pc_svc
    from app.services import apontamento_service as ap_svc
    from datetime import date

    data_str = request.args.get("data",  str(date.today()))
    turno    = request.args.get("turno", "")
    setor    = request.args.get("setor", "")
    linha    = request.args.get("linha", "")
    erro     = None
    planos   = []
    ops      = []
    filtros  = {"setores": [], "linhas": []}
    opcoes   = {}
    fila_smd = []

    try:
        planos   = svc.listar(data_str, turno, setor, linha)
        ops      = svc.ops_disponiveis()
        filtros  = pc_svc.filtros_disponiveis(setor)
        opcoes   = svc.opcoes_linha()
        fila_smd = ap_svc.fila_producao()
    except Exception as e:
        erro = str(e)

    return render_template(
        "pcp/planejamento.html",
        active_menu="pcp_planejamento",
        data_selecionada=data_str,
        turno=turno,
        setor=setor,
        linha=linha,
        planos=planos,
        ops=ops,
        filtros=filtros,
        opcoes=opcoes,
        fila_smd=fila_smd,
        erro=erro,
    )


@bp.route("/pcp/planejamento/criar", methods=["POST"])
@login_required
def pcp_planejamento_criar():
    from flask import request, jsonify
    from flask_login import current_user
    from app.services import planejamento_service as svc

    data = request.get_json(silent=True) or {}
    try:
        resultado = svc.criar(data, username=current_user.username)
        return jsonify({"ok": True, **resultado})
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@bp.route("/pcp/planejamento/<int:plan_id>/editar", methods=["POST"])
@login_required
def pcp_planejamento_editar(plan_id):
    from flask import request, jsonify
    from app.services import planejamento_service as svc

    data = request.get_json(silent=True) or {}
    try:
        resultado = svc.atualizar(plan_id, data)
        return jsonify({"ok": True, **resultado})
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@bp.route("/pcp/planejamento/<int:plan_id>/status", methods=["POST"])
@login_required
def pcp_planejamento_status(plan_id):
    from flask import request, jsonify
    from app.services import planejamento_service as svc

    data = request.get_json(silent=True) or {}
    try:
        svc.atualizar_status(plan_id, data.get("status", ""))
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@bp.route("/pcp/planejamento/<int:plan_id>/excluir", methods=["POST"])
@login_required
def pcp_planejamento_excluir(plan_id):
    from flask import jsonify
    from app.services import planejamento_service as svc

    try:
        svc.excluir(plan_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@bp.route("/pcp/planejamento/plano-de-voo")
@login_required
def pcp_planejamento_plano_de_voo():
    from flask import request, jsonify
    from app.services import planejamento_service as svc
    from datetime import date

    data_str = request.args.get("data", str(date.today()))
    try:
        agrupado = svc.plano_de_voo(data_str)
        serializado = {
            linha: [
                {k: (str(v) if hasattr(v, "strftime") else v) for k, v in item.items()}
                for item in itens
            ]
            for linha, itens in agrupado.items()
        }
        return jsonify(serializado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@bp.route("/pcp/entregas")
@login_required
def pcp_entregas():
    return render_template("pcp/entregas.html", active_menu="pcp_entregas")


# ─── Suporte ─────────────────────────────────────────────────────────────────

@bp.route("/suporte/centro-conhecimento")
@login_required
def suporte_centro_conhecimento():
    try:
        from app.repositories.suporte_repository import list_faq_items
        faqs = list_faq_items()
    except Exception:
        faqs = []
    return render_template(
        "suporte/centro_conhecimento.html",
        active_menu="suporte_centro_conhecimento",
        faqs=faqs,
    )


@bp.route("/suporte/ouvidoria", methods=["GET", "POST"])
@login_required
def suporte_ouvidoria():
    from flask import request, flash, redirect, url_for
    from app.repositories.suporte_repository import create_ouvidoria_message

    if request.method == "POST":
        tipo = request.form.get("tipo", "").strip()
        mensagem = request.form.get("mensagem", "").strip()
        nome_contato = request.form.get("nome_contato", "").strip()

        if not tipo or not mensagem:
            flash("Preencha o tipo e a mensagem.", "danger")
        else:
            try:
                create_ouvidoria_message({
                    "tipo": tipo,
                    "mensagem": mensagem,
                    "nome_contato": nome_contato,
                    "user_id": current_user.id,
                })
                flash("Mensagem enviada com sucesso. Obrigado pelo seu contato.", "success")
            except Exception:
                flash("Erro ao enviar mensagem. Execute a migração 002 no banco.", "danger")
            return redirect(url_for("pages.suporte_ouvidoria"))

    return render_template("suporte/ouvidoria.html", active_menu="suporte_ouvidoria")


@bp.route("/suporte/suporte-especializado", methods=["GET", "POST"])
@login_required
def suporte_especializado():
    from flask import request, flash, redirect, url_for

    try:
        from app.repositories.suporte_repository import (
            get_or_create_ticket,
            list_ticket_messages,
            create_ticket_message,
        )
        ticket = get_or_create_ticket(current_user.id)
    except Exception:
        return render_template(
            "suporte/suporte_especializado.html",
            active_menu="suporte_especializado",
            ticket=None,
            messages=[],
        )

    if request.method == "POST":
        mensagem = request.form.get("mensagem", "").strip()
        if mensagem:
            try:
                create_ticket_message({
                    "ticket_id": ticket["id"],
                    "user_id": current_user.id,
                    "is_support": False,
                    "mensagem": mensagem,
                })
            except Exception:
                flash("Erro ao enviar mensagem.", "danger")
        return redirect(url_for("pages.suporte_especializado"))

    try:
        messages = list_ticket_messages(ticket["id"])
    except Exception:
        messages = []

    return render_template(
        "suporte/suporte_especializado.html",
        active_menu="suporte_especializado",
        ticket=ticket,
        messages=messages,
    )


# ─── Admin ────────────────────────────────────────────────────────────────────

@bp.route("/admin/chamados", methods=["GET"])
@login_required
@admin_required
def admin_chamados():
    from flask import request
    from app.repositories.suporte_repository import list_all_tickets, get_ticket_by_id, list_ticket_messages

    ticket_id = request.args.get("ticket_id", type=int)
    tickets = list_all_tickets()
    selected_ticket = None
    selected_messages = []

    if ticket_id:
        selected_ticket = get_ticket_by_id(ticket_id)
        if selected_ticket:
            selected_messages = list_ticket_messages(ticket_id)

    return render_template(
        "admin/chamados.html",
        active_menu="admin_chamados",
        tickets=tickets,
        selected_ticket=selected_ticket,
        selected_messages=selected_messages,
    )


@bp.route("/admin/chamados/<int:ticket_id>/responder", methods=["POST"])
@login_required
@admin_required
def admin_chamados_responder(ticket_id):
    from flask import request, redirect, url_for
    from app.repositories.suporte_repository import get_ticket_by_id, create_ticket_message

    mensagem = request.form.get("mensagem", "").strip()
    if mensagem and get_ticket_by_id(ticket_id):
        create_ticket_message({
            "ticket_id": ticket_id,
            "user_id": current_user.id,
            "is_support": True,
            "mensagem": mensagem,
        })
    return redirect(url_for("pages.admin_chamados", ticket_id=ticket_id))


@bp.route("/admin/chamados/<int:ticket_id>/fechar", methods=["POST"])
@login_required
@admin_required
def admin_chamados_fechar(ticket_id):
    from flask import redirect, url_for
    from app.repositories.suporte_repository import close_ticket

    close_ticket(ticket_id)
    return redirect(url_for("pages.admin_chamados"))


@bp.route("/admin/backup", methods=["GET", "POST"])
@login_required
@admin_required
def admin_backup():
    from flask import request, flash, redirect, url_for

    try:
        from app.repositories.backup_repository import (
            get_backup_config,
            upsert_backup_config,
            list_backup_logs,
        )
        from app.services.backup_service import trigger_manual_backup
        config = get_backup_config()
        logs = list_backup_logs(limit=50)
    except Exception:
        config = None
        logs = []
        upsert_backup_config = None
        trigger_manual_backup = None

    if request.method == "POST":
        action = request.form.get("action")

        if upsert_backup_config is None or trigger_manual_backup is None:
            flash("Execute a migração 002 no banco antes de usar esta funcionalidade.", "danger")
            return redirect(url_for("pages.admin_backup"))

        if action == "save_config":
            upsert_backup_config({
                "database_url": request.form.get("database_url", "").strip(),
                "frequency": request.form.get("frequency", "daily"),
                "execution_hour": int(request.form.get("execution_hour", 2)),
                "execution_minute": int(request.form.get("execution_minute", 0)),
                "retention_days": int(request.form.get("retention_days", 30)),
                "is_active": request.form.get("is_active") == "1",
            })
            flash("Configuração salva com sucesso.", "success")
            return redirect(url_for("pages.admin_backup"))

        if action == "run_now":
            trigger_manual_backup()
            flash("Backup iniciado em segundo plano.", "info")
            return redirect(url_for("pages.admin_backup"))

    return render_template(
        "admin/backups.html",
        active_menu="admin_backup",
        config=config,
        logs=logs,
    )


# ─── PWA / Legal ─────────────────────────────────────────────────────────────

@bp.route("/privacy-policy")
def privacy_policy():
    return render_template("legal/privacy.html")


@bp.route("/cookie-policy")
def cookie_policy():
    return render_template("legal/cookies.html")


@bp.route("/offline", endpoint="offline_page")
def offline():
    return render_template("offline.html")


@bp.route("/manifest.webmanifest", endpoint="pwa_manifest")
def manifest():
    from flask import current_app, send_from_directory, make_response
    import os

    static_dir = os.path.join(current_app.root_path, "static")
    resp = make_response(send_from_directory(static_dir, "manifest.webmanifest"))
    resp.headers["Content-Type"] = "application/manifest+json; charset=utf-8"
    resp.headers["Cache-Control"] = "no-cache, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp


@bp.route("/sw.js", endpoint="pwa_sw")
def service_worker():
    from flask import current_app, send_from_directory, make_response
    import os

    static_dir = os.path.join(current_app.root_path, "static")
    resp = make_response(send_from_directory(static_dir, "sw.js"))
    resp.headers["Content-Type"] = "application/javascript; charset=utf-8"
    resp.headers["Cache-Control"] = "no-cache, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Service-Worker-Allowed"] = "/"
    return resp
