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


@bp.route("/funcionalidades/resumo-producao")
@login_required
def funcionalidades_resumo_producao():
    from flask import request
    from app.services import resumo_producao_service as svc

    data_inicial = request.args.get("data_inicial", "")
    data_final   = request.args.get("data_final", "")
    turno        = request.args.get("turno", "")
    status       = request.args.get("status", "")

    try:
        resumos = svc.listar(data_inicial, data_final, turno, status, current_user.username)
        erro    = None
    except Exception as e:
        resumos = []
        erro    = str(e)

    return render_template(
        "funcionalidades/resumo_producao_lista.html",
        active_menu="funcionalidades_resumo_producao",
        resumos=resumos,
        data_inicial=data_inicial,
        data_final=data_final,
        turno=turno,
        status=status,
        erro=erro,
    )


@bp.route("/funcionalidades/resumo-producao/novo", methods=["GET", "POST"])
@login_required
def funcionalidades_resumo_producao_novo():
    from flask import request, flash, redirect, url_for
    from app.services import resumo_producao_service as svc
    from app.repositories import linha_config_repository as linha_repo

    if request.method == "POST":
        try:
            resumo_id = svc.criar(request.form, current_user.username)
            flash("Relatório salvo com sucesso.", "success")
            return redirect(url_for("pages.funcionalidades_resumo_producao_editar", resumo_id=resumo_id))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Erro ao salvar o relatório.", "danger")

    try:
        linhas_config = linha_repo.listar_por_setor()
    except Exception:
        linhas_config = {}

    return render_template(
        "funcionalidades/resumo_producao_form.html",
        active_menu="funcionalidades_resumo_producao",
        resumo=None,
        linhas_config=linhas_config,
    )


@bp.route("/funcionalidades/resumo-producao/<int:resumo_id>/editar", methods=["GET", "POST"])
@login_required
def funcionalidades_resumo_producao_editar(resumo_id: int):
    from flask import request, flash, redirect, url_for
    from app.services import resumo_producao_service as svc
    from app.repositories import linha_config_repository as linha_repo

    resumo = svc.buscar_por_id(resumo_id)
    if not resumo:
        flash("Relatório não encontrado.", "warning")
        return redirect(url_for("pages.funcionalidades_resumo_producao"))

    if request.method == "POST":
        try:
            svc.atualizar(resumo_id, request.form)
            flash("Relatório atualizado.", "success")
            return redirect(url_for("pages.funcionalidades_resumo_producao_editar", resumo_id=resumo_id))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Erro ao atualizar o relatório.", "danger")
        resumo = svc.buscar_por_id(resumo_id)

    try:
        linhas_config = linha_repo.listar_por_setor()
    except Exception:
        linhas_config = {}

    return render_template(
        "funcionalidades/resumo_producao_form.html",
        active_menu="funcionalidades_resumo_producao",
        resumo=resumo,
        linhas_config=linhas_config,
    )


@bp.route("/funcionalidades/resumo-producao/<int:resumo_id>/relatorio")
@login_required
def funcionalidades_resumo_producao_relatorio(resumo_id: int):
    from flask import flash, redirect, url_for
    from app.services import resumo_producao_service as svc

    resumo = svc.buscar_por_id(resumo_id)
    if not resumo:
        flash("Relatório não encontrado.", "warning")
        return redirect(url_for("pages.funcionalidades_resumo_producao"))

    return render_template(
        "funcionalidades/resumo_producao_relatorio.html",
        active_menu="funcionalidades_resumo_producao",
        resumo=resumo,
    )


@bp.route("/funcionalidades/resumo-producao/<int:resumo_id>/excluir", methods=["POST"])
@login_required
def funcionalidades_resumo_producao_excluir(resumo_id: int):
    from flask import flash, redirect, url_for
    from app.services import resumo_producao_service as svc

    try:
        svc.excluir(resumo_id)
        flash("Relatório excluído.", "success")
    except Exception:
        flash("Erro ao excluir o relatório.", "danger")
    return redirect(url_for("pages.funcionalidades_resumo_producao"))


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


@bp.route("/smd/monitor-tv")
@login_required
def smd_monitor_tv():
    from app.services import monitor_smd_service as svc
    try:
        dados = svc.get_status_atual()
        erro  = None
    except Exception as e:
        dados = {"linhas": [], "turno_nome": "—", "slots": [], "hoje": "", "atualizado_em": "", "tem_turno": False}
        erro  = str(e)
    return render_template(
        "producao/monitor_smd_tv.html",
        active_menu="smd_monitor_tv",
        dados=dados,
        erro=erro,
    )


# ─── Engenharia ──────────────────────────────────────────────────────────────

@bp.route("/engenharia/folha-cronometragem")
@login_required
def engenharia_folha_crono():
    return render_template("engenharia/folha_cronometragem.html", active_menu="engenharia_folha_crono")


# ─── PCP ─────────────────────────────────────────────────────────────────────

@bp.route("/pcp/lancamento-producao", methods=["GET"])
@login_required
@admin_required
def pcp_lancamento_producao():
    from flask import request
    from app.services import producao_manual_service as svc

    data_inicial_pad, data_final_pad = svc.data_padrao()

    data_inicial = request.args.get("dataInicial", data_inicial_pad)
    data_final   = request.args.get("dataFinal",   data_final_pad)
    setor        = request.args.get("setor",  "")
    linha        = request.args.get("linha",  "")
    turno        = request.args.get("turno",  "")

    try:
        registros = svc.listar(data_inicial, data_final, setor, linha, turno)
        filtros   = svc.filtros_disponiveis()
        erro      = None
    except Exception as e:
        registros = []
        filtros   = {"setores": [], "linhas_por_setor": {}}
        erro      = str(e)

    return render_template(
        "pcp/lancamento_producao.html",
        active_menu="pcp_lancamento_producao",
        data_inicial=data_inicial,
        data_final=data_final,
        setor=setor,
        linha=linha,
        turno=turno,
        registros=registros,
        filtros=filtros,
        erro=erro,
    )


@bp.route("/pcp/lancamento-producao/inserir", methods=["POST"])
@login_required
@admin_required
def pcp_lancamento_producao_inserir():
    from flask import request, redirect, url_for, flash
    from app.services import producao_manual_service as svc

    try:
        svc.inserir(request.form)
        flash("Produção lançada com sucesso.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Erro inesperado ao salvar o lançamento.", "danger")

    return redirect(url_for("pages.pcp_lancamento_producao"))


@bp.route("/pcp/lancamento-producao/excluir", methods=["POST"])
@login_required
@admin_required
def pcp_lancamento_producao_excluir():
    from flask import request, redirect, url_for, flash
    from app.services import producao_manual_service as svc

    try:
        registro_id = int(request.form.get("registro_id", 0))
        svc.excluir(registro_id)
        flash("Lançamento excluído.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Erro inesperado ao excluir o lançamento.", "danger")

    return redirect(url_for("pages.pcp_lancamento_producao"))


@bp.route("/pcp/roteiros")
@login_required
@admin_required
def pcp_roteiros():
    from flask import request
    from app.services import roteiro_service as svc

    cliente = request.args.get("cliente", "")

    try:
        roteiros          = svc.listar(cliente)
        clientes_roteiros = svc.clientes_roteiros()
        clientes_modelos  = svc.clientes_modelos()
        erro              = None
    except Exception as e:
        roteiros          = []
        clientes_roteiros = []
        clientes_modelos  = []
        erro              = str(e)

    return render_template(
        "pcp/roteiros.html",
        active_menu="pcp_roteiros",
        cliente=cliente,
        roteiros=roteiros,
        clientes_roteiros=clientes_roteiros,
        clientes_modelos=clientes_modelos,
        erro=erro,
    )


@bp.route("/pcp/roteiros/criar", methods=["POST"])
@login_required
@admin_required
def pcp_roteiros_criar():
    from flask import request, jsonify
    from app.services import roteiro_service as svc
    import json

    try:
        dados = request.get_json(force=True)
        roteiro_id = svc.criar(dados)
        return jsonify({"ok": True, "id": roteiro_id})
    except ValueError as e:
        return jsonify({"ok": False, "erro": str(e)}), 400
    except Exception:
        return jsonify({"ok": False, "erro": "Erro inesperado ao criar roteiro."}), 500


@bp.route("/pcp/roteiros/<int:roteiro_id>/editar", methods=["POST"])
@login_required
@admin_required
def pcp_roteiros_editar(roteiro_id):
    from flask import request, jsonify
    from app.services import roteiro_service as svc

    try:
        dados = request.get_json(force=True)
        svc.editar(roteiro_id, dados)
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"ok": False, "erro": str(e)}), 400
    except Exception:
        return jsonify({"ok": False, "erro": "Erro inesperado ao editar roteiro."}), 500


@bp.route("/pcp/roteiros/<int:roteiro_id>/excluir", methods=["POST"])
@login_required
@admin_required
def pcp_roteiros_excluir(roteiro_id):
    from flask import jsonify
    from app.services import roteiro_service as svc

    try:
        svc.excluir(roteiro_id)
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"ok": False, "erro": str(e)}), 400
    except Exception:
        return jsonify({"ok": False, "erro": "Erro inesperado ao excluir roteiro."}), 500


@bp.route("/pcp/roteiros/<int:roteiro_id>/modelos", methods=["GET"])
@login_required
@admin_required
def pcp_roteiros_modelos(roteiro_id):
    from flask import jsonify
    from app.services import roteiro_service as svc

    try:
        modelos = svc.modelos_do_roteiro(roteiro_id)
        return jsonify({"ok": True, "modelos": modelos})
    except Exception:
        return jsonify({"ok": False, "erro": "Erro ao carregar modelos."}), 500


@bp.route("/pcp/roteiros/<int:roteiro_id>/vincular-modelo", methods=["POST"])
@login_required
@admin_required
def pcp_roteiros_vincular_modelo(roteiro_id):
    from flask import request, jsonify
    from app.services import roteiro_service as svc

    try:
        dados = request.get_json(force=True)
        svc.vincular_modelo(roteiro_id, dados.get("codigo", ""))
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"ok": False, "erro": str(e)}), 400
    except Exception:
        return jsonify({"ok": False, "erro": "Erro ao vincular modelo."}), 500


@bp.route("/pcp/roteiros/<int:roteiro_id>/desvincular-modelo", methods=["POST"])
@login_required
@admin_required
def pcp_roteiros_desvincular_modelo(roteiro_id):
    from flask import request, jsonify
    from app.services import roteiro_service as svc

    try:
        dados = request.get_json(force=True)
        svc.desvincular_modelo(roteiro_id, dados.get("codigo", ""))
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"ok": False, "erro": str(e)}), 400
    except Exception:
        return jsonify({"ok": False, "erro": "Erro ao desvincular modelo."}), 500


@bp.route("/pcp/roteiros/<int:roteiro_id>/codigos-cliente")
@login_required
@admin_required
def pcp_roteiros_codigos_cliente(roteiro_id):
    from flask import jsonify
    from app.services import roteiro_service as svc

    try:
        roteiro = svc.buscar(roteiro_id)
        codigos = svc.codigos_por_cliente(roteiro["cliente"])
        return jsonify({"ok": True, "codigos": codigos})
    except ValueError as e:
        return jsonify({"ok": False, "erro": str(e)}), 404
    except Exception:
        return jsonify({"ok": False, "erro": "Erro ao carregar códigos."}), 500


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
    from app.services import linha_lider_service as lider_svc

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
        elif acao == "salvar_lider":
            try:
                lider_svc.salvar(request.form)
                flash("Responsável/HC salvo.", "success")
            except ValueError as e:
                flash(str(e), "danger")
            except Exception as e:
                flash(str(e), "danger")
        elif acao == "excluir_lider":
            try:
                lider_svc.excluir(
                    request.form.get("setor", ""),
                    request.form.get("linha", ""),
                    request.form.get("turno", ""),
                )
                flash("Responsável/HC removido.", "success")
            except Exception as e:
                flash(str(e), "danger")
        return redirect(url_for("pages.config_paradas"))

    try:
        paradas = svc.listar_por_setor()
        opcoes  = svc.opcoes_linha()
    except Exception as e:
        erro = str(e)

    lideres = {}
    try:
        lideres = lider_svc.listar_por_setor()
    except Exception:
        pass

    return render_template(
        "config/paradas.html",
        active_menu="config_paradas",
        paradas=paradas,
        opcoes=opcoes,
        tipos=["INTERVALO_1", "INTERVALO_2", "GINASTICA", "DDS", "REFEICAO", "SETUP", "SMD_5S", "OUTROS"],
        lideres=lideres,
        erro=erro,
    )


# ─── PCP ─────────────────────────────────────────────────────────────────────

@bp.route("/pcp/controle-ops", methods=["GET", "POST"])
@login_required
def pcp_controle_ops():
    from flask import request, flash, redirect, url_for
    from app.services import controle_ops_service as svc
    from app.services import roteiro_service as roteiro_svc

    erro     = None
    ops      = []
    filiais  = []
    roteiros = []
    filial   = request.args.get("filial", "")
    status   = request.args.get("status", "")
    setor    = request.args.get("setor",  "")

    if request.method == "POST":
        try:
            result = svc.cadastrar(request.form)
            if result["tipo"] == "roteiro":
                flash(f"{result['n_ops']} OPs criadas pelo roteiro \"{result['nome']}\".", "success")
            elif result["tipo"] == "roteiro_padrao":
                flash("Roteiro criado: 3 OPs cadastradas (PTH, IM, SMD).", "success")
            else:
                flash("OP cadastrada com sucesso.", "success")
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Erro ao cadastrar. Verifique se a tabela foi criada.", "danger")
        return redirect(url_for("pages.pcp_controle_ops"))

    try:
        ops      = svc.listar(filial, status, setor)
        filiais  = svc.filiais_disponiveis()
        roteiros = roteiro_svc.listar()
    except Exception as e:
        erro = str(e)

    return render_template(
        "pcp/controle_ops.html",
        active_menu="pcp_controle_ops",
        ops=ops,
        filiais=filiais,
        roteiros=roteiros,
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
        apontamentos   = svc.listar_agrupado(data_inicial, data_final, setor, linha, turno)
        ops            = svc.ops_abertas("")
        filtros        = pc_svc.filtros_disponiveis(setor)
        producao_total = sum(ap["producao_total"] or 0 for ap in apontamentos)
        erro           = None
    except Exception as e:
        apontamentos   = []
        ops            = []
        filtros        = {"setores": [], "linhas": []}
        producao_total = 0
        erro           = str(e)

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
        producao_total=producao_total,
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


@bp.route("/pcp/apontamento/corrigir-modelo", methods=["POST"])
@login_required
def pcp_apontamento_corrigir_modelo():
    from flask import request, jsonify
    from app.services import apontamento_service as svc

    data = request.get_json(silent=True) or {}
    try:
        svc.corrigir_modelo(
            data.get("data", ""),
            data.get("turno", ""),
            data.get("setor", ""),
            data.get("linha", ""),
            data.get("modelo_atual", ""),
            data.get("modelo_novo", ""),
        )
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

    planos_agrupados = []
    resumo           = []

    try:
        planos           = svc.listar(data_str, turno, setor, linha)
        ops              = svc.ops_disponiveis()
        filtros          = pc_svc.filtros_disponiveis(setor)
        opcoes           = svc.opcoes_linha()
        fila_smd         = ap_svc.fila_producao()
        planos_agrupados = svc.planos_agrupados_por_linha(data_str)
        resumo           = svc.resumo_producao(data_str, turno)
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
        planos_agrupados=planos_agrupados,
        resumo=resumo,
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


@bp.route("/pcp/planejamento/criar-lote", methods=["POST"])
@login_required
def pcp_planejamento_criar_lote():
    from flask import request, jsonify
    from flask_login import current_user
    from app.services import planejamento_service as svc

    body = request.get_json(silent=True) or {}
    try:
        resultados = svc.criar_lote(
            header=body.get("header", {}),
            modelos=body.get("modelos", []),
            username=current_user.username,
        )
        return jsonify({"ok": True, "resultados": resultados})
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


@bp.route("/pcp/planejamento/buscar-meta")
@login_required
def pcp_planejamento_buscar_meta():
    from flask import request, jsonify, current_app
    from app.repositories import modelos_repository as mr
    from app.services import planejamento_service as svc

    codigo = request.args.get("codigo", "").strip().upper()
    setor  = request.args.get("setor",  "").strip().upper()
    linha  = request.args.get("linha",  "").strip().upper()
    fase   = request.args.get("fase",   "").strip().upper()

    try:
        result_meta = mr.buscar_meta_com_fase(codigo, setor, fase) if codigo else {"meta": None, "fase_encontrada": None}
        meta = result_meta["meta"]
        fase_encontrada = result_meta["fase_encontrada"]
        setup = svc.setup_sugerido(setor, linha)
        result = {"meta": meta, "setup_sugerido": setup}
        if fase_encontrada:
            result["fase_encontrada"] = fase_encontrada
        if meta is None and codigo:
            result["_debug"] = mr.buscar_candidatos_diagnostico(codigo)
        return jsonify(result)
    except Exception as e:
        current_app.logger.exception(
            "buscar_meta falhou: codigo=%s setor=%s fase=%s", codigo, setor, fase
        )
        return jsonify({"meta": None, "setup_sugerido": 0, "_erro": str(e)}), 500


@bp.route("/pcp/planejamento/plano-detalhado")
@login_required
def pcp_planejamento_plano_detalhado():
    from flask import request, jsonify
    from app.services import planejamento_service as svc
    from app.repositories import planejamento_repository as repo_plan

    data_str = request.args.get("data",  "")
    turno    = request.args.get("turno", "")
    setor    = request.args.get("setor", "")
    linha    = request.args.get("linha", "")

    if not data_str or not turno or not linha:
        return jsonify({"erro": "data, turno e linha são obrigatórios"}), 400

    try:
        planos     = repo_plan.listar_plano_de_voo(data_str, turno=turno, setor=setor, linha=linha)
        intervalos = repo_plan.turno_intervalos(turno)
        paradas    = repo_plan.paradas_da_linha(setor, linha)
        slots      = svc.gerar_plano_hora_a_hora(
            [dict(p) for p in planos],
            [dict(i) for i in intervalos],
            [dict(p) for p in paradas],
            data_str,
        )
        return jsonify({"slots": slots})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@bp.route("/pcp/planejamento/plano-de-voo/imprimir")
@login_required
def pcp_planejamento_plano_voo_imprimir():
    from flask import request
    from app.services import planejamento_service as svc
    from datetime import date

    data_str = request.args.get("data",  str(date.today()))
    turno    = request.args.get("turno", "")
    setor    = request.args.get("setor", "")
    linha    = request.args.get("linha", "")

    try:
        dados = svc.dados_impressao_plano_voo(data_str, turno, setor, linha)
    except Exception as e:
        dados = {"slots": [], "data": data_str, "info": {}, "erro": str(e)}

    return render_template("pcp/plano_voo_print.html", **dados)


@bp.route("/pcp/planejamento/plano-de-voo/imprimir-todos")
@login_required
def pcp_planejamento_plano_voo_imprimir_todos():
    from flask import request
    from app.services import planejamento_service as svc
    from datetime import date

    data_str     = request.args.get("data",  str(date.today()))
    turno_filtro = request.args.get("turno", "")

    grupos = svc.planos_agrupados_por_linha(data_str)
    todos = []
    for g in grupos:
        if turno_filtro and g["turno"] != turno_filtro:
            continue
        try:
            dados = svc.dados_impressao_plano_voo(data_str, g["turno"], g["setor"], g["linha"])
            todos.append(dados)
        except Exception:
            pass

    return render_template("pcp/plano_voo_print_todos.html", planos=todos, data=data_str)


@bp.route("/pcp/planejamento/resumo/imprimir")
@login_required
def pcp_planejamento_resumo_imprimir():
    from flask import request
    from app.services import planejamento_service as svc
    from datetime import date, datetime

    data_str     = request.args.get("data",  str(date.today()))
    turno        = request.args.get("turno", "")
    setor_filtro = request.args.get("setor", "")

    try:
        resumo = svc.resumo_producao(data_str, turno, setor_filtro)
    except Exception as e:
        resumo = []

    dias_semana = ["Segunda-Feira", "Terça-Feira", "Quarta-Feira",
                   "Quinta-Feira", "Sexta-Feira", "Sábado", "Domingo"]
    try:
        dt         = datetime.strptime(data_str, "%Y-%m-%d")
        dia_semana = dias_semana[dt.weekday()]
        data_fmt   = dt.strftime("%d/%m/%Y")
    except ValueError:
        dia_semana = ""
        data_fmt   = data_str

    return render_template(
        "pcp/resumo_producao_print.html",
        resumo=resumo,
        data=data_str,
        data_fmt=data_fmt,
        dia_semana=dia_semana,
        turno=turno,
        setor_filtro=setor_filtro,
    )


@bp.route("/pcp/entregas")
@login_required
def pcp_entregas():
    import calendar
    from datetime import date
    from flask import request
    from app.services import entregas_service as svc

    hoje = date.today()
    ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
    default_inicial = hoje.replace(day=1).strftime("%Y-%m-%d")
    default_final   = hoje.replace(day=ultimo_dia).strftime("%Y-%m-%d")

    tab          = request.args.get("tab", "pedido")
    status       = request.args.get("status", "")
    data_inicial = request.args.get("dataInicial", default_inicial)
    data_final   = request.args.get("dataFinal", default_final)
    data_hoje    = svc.data_padrao()

    try:
        pedidos   = svc.listar_pedidos(status, "", data_inicial, data_final)
        entregas  = svc.listar_entregas()
        equipe    = svc.listar_equipe()
        erro      = None
    except Exception as e:
        pedidos  = []
        entregas = []
        equipe   = []
        erro     = str(e)

    return render_template(
        "pcp/entregas.html",
        active_menu="logistica_entregas" if tab == "logistica" else "pcp_entregas",
        tab=tab,
        pedidos=pedidos,
        entregas=entregas,
        equipe=equipe,
        data_hoje=data_hoje,
        status_label=svc.STATUS_LABEL,
        status_cor=svc.STATUS_COR,
        status_filter=status,
        data_inicial=data_inicial,
        data_final=data_final,
        erro=erro,
    )


@bp.route("/pcp/entregas/locais", methods=["GET"])
@login_required
def pcp_entregas_locais():
    from flask import request, jsonify
    from app.services import locais_entrega_service as svc

    cliente = request.args.get("cliente", "")
    locais = svc.listar_locais(cliente)
    return jsonify({"ok": True, "locais": [dict(l) for l in locais]})


@bp.route("/pcp/entregas/locais/novo", methods=["POST"])
@login_required
def pcp_entregas_locais_novo():
    from flask import request, jsonify
    from app.services import locais_entrega_service as svc

    data = request.get_json(silent=True) or {}
    try:
        local_id = svc.criar_local(
            data.get("cliente", ""),
            data.get("nome_local", ""),
            data.get("endereco", ""),
            float(data["lat"]) if data.get("lat") else None,
            float(data["lng"]) if data.get("lng") else None,
        )
        return jsonify({"ok": True, "id": local_id})
    except (ValueError, Exception) as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/pcp/entregas/locais/<int:local_id>/editar", methods=["POST"])
@login_required
def pcp_entregas_locais_editar(local_id):
    from flask import request, jsonify
    from app.services import locais_entrega_service as svc

    data = request.get_json(silent=True) or {}
    try:
        svc.atualizar_local(
            local_id,
            data.get("cliente", ""),
            data.get("nome_local", ""),
            data.get("endereco", ""),
            float(data["lat"]) if data.get("lat") else None,
            float(data["lng"]) if data.get("lng") else None,
        )
        return jsonify({"ok": True})
    except (ValueError, Exception) as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/pcp/entregas/locais/<int:local_id>/excluir", methods=["POST"])
@login_required
def pcp_entregas_locais_excluir(local_id):
    from flask import jsonify
    from app.services import locais_entrega_service as svc

    try:
        svc.excluir_local(local_id)
        return jsonify({"ok": True})
    except (ValueError, Exception) as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/pcp/entregas/pedido/novo", methods=["POST"])
@login_required
def pcp_entregas_pedido_novo():
    from flask import request, jsonify
    from app.services import entregas_service as svc

    data = request.get_json(silent=True) or {}
    try:
        local_id = int(data["local_entrega_id"]) if data.get("local_entrega_id") else None
        pedido_id = svc.criar_pedido(
            data.get("numero_pedido", ""),
            data.get("cliente", ""),
            data.get("modelo", ""),
            data.get("familia", ""),
            int(data.get("quantidade", 0)),
            data.get("data_pedido", ""),
            data.get("data_entrega", ""),
            data.get("observacao", ""),
            local_id,
        )
        return jsonify({"ok": True, "id": pedido_id})
    except (ValueError, Exception) as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/pcp/entregas/pedido/<int:pedido_id>/editar", methods=["POST"])
@login_required
def pcp_entregas_pedido_editar(pedido_id):
    from flask import request, jsonify
    from app.services import entregas_service as svc

    data = request.get_json(silent=True) or {}
    try:
        local_id = int(data["local_entrega_id"]) if data.get("local_entrega_id") else None
        svc.atualizar_pedido(
            pedido_id,
            data.get("numero_pedido", ""),
            data.get("cliente", ""),
            data.get("modelo", ""),
            data.get("familia", ""),
            int(data.get("quantidade", 0)),
            data.get("data_pedido", ""),
            data.get("data_entrega", ""),
            data.get("observacao", ""),
            local_id,
        )
        return jsonify({"ok": True})
    except (ValueError, Exception) as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/pcp/entregas/pedido/<int:pedido_id>/excluir", methods=["POST"])
@login_required
def pcp_entregas_pedido_excluir(pedido_id):
    from flask import jsonify
    from app.services import entregas_service as svc

    try:
        svc.excluir_pedido(pedido_id)
        return jsonify({"ok": True})
    except (ValueError, Exception) as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/pcp/entregas/pedido/<int:pedido_id>/remessas", methods=["GET"])
@login_required
def pcp_entregas_pedido_remessas(pedido_id):
    from flask import jsonify
    from app.services import entregas_service as svc

    try:
        remessas = svc.listar_remessas_pedido(pedido_id)
        return jsonify({"ok": True, "remessas": [dict(r) for r in remessas]})
    except Exception as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/pcp/entregas/entrega/nova", methods=["POST"])
@login_required
def pcp_entregas_entrega_nova():
    from flask import request, jsonify
    from app.services import entregas_service as svc

    data = request.get_json(silent=True) or {}
    try:
        entrega_id = svc.criar_entrega(
            int(data.get("pedido_id", 0)),
            int(data.get("quantidade", 0)),
            data.get("nota_fiscal", ""),
        )
        return jsonify({"ok": True, "id": entrega_id})
    except (ValueError, Exception) as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/pcp/entregas/entrega/<int:entrega_id>/status", methods=["POST"])
@login_required
def pcp_entregas_entrega_status(entrega_id):
    from flask import request, jsonify
    from app.services import entregas_service as svc

    data = request.get_json(silent=True) or {}
    try:
        motorista_id = int(data["motorista_id"]) if data.get("motorista_id") else None
        svc.atualizar_status_entrega(
            entrega_id,
            data.get("status", ""),
            data.get("nota_fiscal"),
            motorista_id,
        )
        membro_ids = [int(x) for x in data.get("membro_ids", []) if x]
        if membro_ids:
            svc.sincronizar_equipe_entrega(entrega_id, membro_ids)
        return jsonify({"ok": True})
    except (ValueError, Exception) as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/pcp/entregas/entrega/<int:entrega_id>/posicao", methods=["GET"])
@login_required
def pcp_entregas_entrega_posicao(entrega_id):
    from flask import jsonify
    from app.services import entregas_service as svc

    entrega = svc.buscar_entrega(entrega_id)
    if not entrega:
        return jsonify({"erro": "Não encontrado"}), 404
    return jsonify({
        "ok": True,
        "lat": float(entrega["lat"]) if entrega["lat"] else None,
        "lng": float(entrega["lng"]) if entrega["lng"] else None,
        "localizacao_em": entrega["localizacao_em"].strftime("%d/%m/%Y %H:%M") if entrega["localizacao_em"] else None,
    })


@bp.route("/pcp/entregas/entrega/<int:entrega_id>/localizacao", methods=["POST"])
@login_required
def pcp_entregas_entrega_localizacao(entrega_id):
    from flask import request, jsonify
    from app.services import entregas_service as svc

    data = request.get_json(silent=True) or {}
    try:
        svc.atualizar_localizacao(
            entrega_id,
            float(data.get("lat", 0)),
            float(data.get("lng", 0)),
        )
        return jsonify({"ok": True})
    except (ValueError, Exception) as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/logistica")
@login_required
def logistica_resumo():
    from flask import request
    from app.services import entregas_service as svc

    data   = request.args.get("data", svc.data_padrao())
    resumo = svc.resumo_apontamento_logistica(data)
    equipe = svc.listar_equipe()

    return render_template(
        "logistica/resumo.html",
        active_menu="logistica_resumo",
        data=data,
        resumo=resumo,
        equipe=equipe,
    )


@bp.route("/logistica/equipe/novo", methods=["POST"])
@login_required
def logistica_equipe_novo():
    from flask import request, jsonify
    from app.services import entregas_service as svc

    data = request.get_json(silent=True) or {}
    try:
        membro_id = svc.criar_membro_equipe(
            data.get("nome", ""),
            data.get("tipo", ""),
            data.get("telefone", ""),
        )
        return jsonify({"ok": True, "id": membro_id})
    except (ValueError, Exception) as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/logistica/equipe/<int:membro_id>/excluir", methods=["POST"])
@login_required
def logistica_equipe_excluir(membro_id):
    from flask import jsonify
    from app.services import entregas_service as svc

    try:
        svc.desativar_membro_equipe(membro_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"erro": str(e)}), 400


@bp.route("/logistica/rastrear/<int:entrega_id>")
@login_required
def logistica_rastrear(entrega_id):
    from flask import abort
    from app.services import entregas_service as svc

    entrega = svc.buscar_entrega(entrega_id)
    if not entrega:
        abort(404)

    return render_template(
        "logistica/rastrear.html",
        active_menu="logistica_resumo",
        entrega=entrega,
    )


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
