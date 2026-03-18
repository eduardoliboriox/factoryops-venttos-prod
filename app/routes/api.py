from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.services import modelos_service, production_lines_service, time_studies_service
from app.services.employees_service import buscar_funcionario
from app.auth.service import confirm_employee_extra


bp = Blueprint("api", __name__)


@bp.route("/modelos", methods=["GET"])
@login_required
def listar():
    return jsonify(modelos_service.listar_modelos())


@bp.route("/modelos", methods=["POST"])
@login_required
def cadastrar():
    return jsonify(modelos_service.cadastrar_modelo(request.form, user=current_user))


@bp.route("/modelos", methods=["PUT"])
@login_required
def atualizar_modelo():
    return jsonify(modelos_service.atualizar_modelo(request.form, user=current_user))


@bp.route("/modelos", methods=["DELETE"])
@login_required
def excluir():
    return jsonify(modelos_service.excluir_modelo(request.form, user=current_user))


@bp.route("/modelos/history", methods=["GET"])
@login_required
def modelos_history():
    codigo = request.args.get("codigo", "").strip()
    fase = request.args.get("fase", "").strip()
    linha = request.args.get("linha", "").strip()
    limit = int(request.args.get("limit", "50") or "50")

    if not codigo or not fase:
        return jsonify([])

    data = modelos_service.listar_historico_modelo(codigo=codigo, fase=fase, linha=linha, limit=limit)
    return jsonify(data)


@bp.route("/modelos/calculo_rapido", methods=["POST"])
def api_calculo_rapido():
    dados = request.form
    meta_hora = dados.get("meta_hora")
    minutos = dados.get("minutos")
    blank = dados.get("blank")

    if not meta_hora or not minutos:
        return jsonify({"sucesso": False, "erro": "Meta/hora e minutos são obrigatórios"}), 400

    try:
        resultado = modelos_service.calculo_rapido(meta_hora, minutos, blank)
        return jsonify({"sucesso": True, "dados": resultado})
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro no cálculo"}), 400


@bp.route("/smt/calcular_meta", methods=["POST"])
def api_smt_calcular_meta():
    tempo_montagem = request.form.get("tempo_montagem")
    blank = request.form.get("blank")

    if not tempo_montagem or not blank:
        return jsonify({"sucesso": False, "erro": "Informe tempo de montagem e blank"}), 400

    return jsonify(modelos_service.calcular_meta_smt(tempo_montagem, blank))


@bp.route("/smt/calcular_tempo", methods=["POST"])
def api_smt_calcular_tempo():
    meta_hora = request.form.get("meta_hora")
    blank = request.form.get("blank")

    if not meta_hora or not blank:
        return jsonify({"sucesso": False, "erro": "Informe meta/hora e blank"}), 400

    return jsonify(modelos_service.calcular_tempo_smt_inverso(meta_hora, blank))


@bp.route("/calcular_perda", methods=["POST"])
def api_calcular_perda():
    meta_hora = request.form.get("meta_hora")
    producao_real = request.form.get("producao_real")

    if not meta_hora or not producao_real:
        return jsonify({"erro": "Dados incompletos"}), 400

    return jsonify(modelos_service.calcular_perda_producao(meta_hora, producao_real))


@bp.route("/employees/<matricula>", methods=["GET"])
def api_employee_lookup(matricula):
    return jsonify(buscar_funcionario(matricula))


@bp.route("/auth/confirm-extra", methods=["POST"])
def api_confirm_extra():
    data = request.get_json() or {}

    matricula = data.get("matricula")
    password = data.get("password")

    if not matricula or not password:
        return jsonify({
            "success": False,
            "error": "Dados incompletos"
        }), 400

    result = confirm_employee_extra(matricula, password)
    return jsonify(result), (200 if result["success"] else 401)


@bp.route("/time-studies", methods=["GET"])
@login_required
def time_studies_list():
    limit = int(request.args.get("limit", "50") or "50")
    data = time_studies_service.list_studies(limit=limit)
    return jsonify(data)


@bp.route("/time-studies", methods=["POST"])
@login_required
def time_studies_create():
    try:
        study = time_studies_service.create_study(request.form, user=current_user)
        return jsonify({"sucesso": True, "study": study})
    except ValueError as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 400
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro ao criar estudo"}), 500


@bp.route("/time-studies/<int:study_id>", methods=["GET"])
@login_required
def time_studies_get(study_id: int):
    detail = time_studies_service.get_study_detail(study_id)
    if not detail:
        return jsonify({"sucesso": False, "erro": "Estudo não encontrado"}), 404
    return jsonify({"sucesso": True, **detail})


@bp.route("/time-studies/<int:study_id>", methods=["DELETE"])
@login_required
def time_studies_delete(study_id: int):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"sucesso": False, "erro": "Apenas administradores podem excluir estudos."}), 403

    try:
        time_studies_service.delete_study(study_id)
        return jsonify({"sucesso": True})
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro ao excluir estudo"}), 500


@bp.route("/time-studies/<int:study_id>/operations", methods=["POST"])
@login_required
def time_studies_add_operation(study_id: int):
    try:
        op = time_studies_service.add_operation(study_id, request.form)
        return jsonify({"sucesso": True, "operation": op})
    except ValueError as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 400
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro ao adicionar operação"}), 500


@bp.route("/time-studies/operations/<int:op_id>", methods=["PUT"])
@login_required
def time_studies_update_operation(op_id: int):
    data = request.get_json(silent=True) or {}
    try:
        op = time_studies_service.update_operation(op_id, data)
        return jsonify({"sucesso": True, "operation": op})
    except ValueError as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 400
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro ao atualizar operação"}), 500


@bp.route("/time-studies/operations/<int:op_id>", methods=["DELETE"])
@login_required
def time_studies_delete_operation(op_id: int):
    try:
        time_studies_service.delete_operation(op_id)
        return jsonify({"sucesso": True})
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro ao excluir operação"}), 500


@bp.route("/production/sectors", methods=["GET"])
@login_required
def production_sectors():
    return jsonify({
        "sucesso": True,
        "sectors": production_lines_service.list_sectors()
    })


@bp.route("/production/lines", methods=["GET"])
@login_required
def production_lines():
    setor = request.args.get("setor", "").strip()
    return jsonify({
        "sucesso": True,
        "setor": setor,
        "lines": production_lines_service.list_lines_by_sector(setor)
    })


@bp.route("/push/vapid-public-key", methods=["GET"])
@login_required
def push_vapid_public_key():
    from flask import current_app
    key = current_app.config.get("VAPID_PUBLIC_KEY")
    if not key:
        return jsonify({"sucesso": False, "erro": "Push não configurado"}), 503
    return jsonify({"sucesso": True, "key": key})


@bp.route("/push/subscribe", methods=["POST"])
@login_required
def push_subscribe():
    from app.repositories import push_repository

    data = request.get_json(silent=True) or {}
    endpoint = (data.get("endpoint") or "").strip()
    keys = data.get("keys") or {}
    p256dh = (keys.get("p256dh") or "").strip()
    auth = (keys.get("auth") or "").strip()

    if not endpoint or not p256dh or not auth:
        return jsonify({"sucesso": False, "erro": "Dados de subscription inválidos"}), 400

    user_id = getattr(current_user, "id", None)

    try:
        push_repository.upsert_subscription(
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_id=user_id,
        )
        return jsonify({"sucesso": True})
    except Exception as exc:
        return jsonify({"sucesso": False, "erro": str(exc)}), 500


@bp.route("/push/unsubscribe", methods=["POST"])
@login_required
def push_unsubscribe():
    from app.repositories import push_repository

    data = request.get_json(silent=True) or {}
    endpoint = (data.get("endpoint") or "").strip()

    if not endpoint:
        return jsonify({"sucesso": False, "erro": "Endpoint ausente"}), 400

    try:
        push_repository.delete_subscription(endpoint)
        return jsonify({"sucesso": True})
    except Exception as exc:
        return jsonify({"sucesso": False, "erro": str(exc)}), 500


@bp.route("/push/diagnostico", methods=["GET"])
@login_required
def push_diagnostico():
    from flask import current_app
    from app.repositories import push_repository

    vapid_public = current_app.config.get("VAPID_PUBLIC_KEY")
    vapid_private = current_app.config.get("VAPID_PRIVATE_KEY")
    vapid_email = current_app.config.get("VAPID_CLAIMS_EMAIL")

    try:
        subs = push_repository.list_all_subscriptions()
        total_subs = len(subs)
        table_ok = True
        table_error = None
    except Exception as exc:
        total_subs = 0
        table_ok = False
        table_error = str(exc)

    return jsonify({
        "vapid_public_key_configurada": bool(vapid_public),
        "vapid_public_key_preview": (vapid_public[:20] + "...") if vapid_public else None,
        "vapid_private_key_configurada": bool(vapid_private),
        "vapid_email": vapid_email,
        "tabela_push_subscriptions_ok": table_ok,
        "tabela_erro": table_error,
        "total_subscriptions": total_subs,
    })


@bp.route("/push/test", methods=["POST"])
@login_required
def push_test():
    from app.services.notification_service import notify_all

    resultado = notify_all(
        title="Teste de notificação",
        body="Se você está vendo isso, as notificações push estão funcionando.",
        url="/smt/modelos",
    )
    return jsonify({"sucesso": True, "resultado": resultado})


@bp.route("/profile/avatar", methods=["POST"])
@login_required
def upload_avatar():
    file = request.files.get("avatar")
    if not file:
        return jsonify({"sucesso": False, "erro": "Nenhuma imagem enviada"}), 400

    try:
        from app.auth.service import save_profile_image
        path = save_profile_image(current_user.id, file)
        return jsonify({"sucesso": True, "url": f"/static/{path}"})
    except ValueError as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 400
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro ao salvar imagem"}), 500


@bp.route("/profile/avatar/remove", methods=["POST"])
@login_required
def remove_avatar():
    try:
        from app.auth.service import remove_profile_image
        remove_profile_image(current_user.id)
        return jsonify({"sucesso": True})
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro ao remover foto"}), 500


# ─── Medição Pasta de Solda ───────────────────────────────────────────────────

@bp.route("/medicao-pasta/registros", methods=["GET"])
@login_required
def medicao_pasta_list():
    from app.services import medicao_pasta_service
    data  = request.args.get("data") or None
    setor = request.args.get("setor") or None
    linha = request.args.get("linha") or None
    return jsonify(medicao_pasta_service.listar_registros(data=data, setor=setor, linha=linha))


@bp.route("/medicao-pasta/registros", methods=["POST"])
@login_required
def medicao_pasta_create():
    from app.services import medicao_pasta_service
    data = request.get_json(silent=True) or {}
    try:
        registro = medicao_pasta_service.criar_registro(data, current_user.id)
        return jsonify({"sucesso": True, "id": registro["id"], "doc_id": registro.get("doc_id")}), 201
    except ValueError as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 400
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro ao salvar medição"}), 500


@bp.route("/medicao-pasta/registros/<int:registro_id>", methods=["GET"])
@login_required
def medicao_pasta_get(registro_id: int):
    from app.services import medicao_pasta_service
    result = medicao_pasta_service.buscar_registro(registro_id)
    if not result:
        return jsonify({"sucesso": False, "erro": "Registro não encontrado"}), 404
    return jsonify(result)


@bp.route("/medicao-pasta/registros/<int:registro_id>", methods=["PATCH"])
@login_required
def medicao_pasta_update(registro_id: int):
    from app.services import medicao_pasta_service
    data = request.get_json(silent=True) or {}
    try:
        medicao_pasta_service.atualizar_registro(registro_id, data)
        return jsonify({"sucesso": True})
    except ValueError as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 404
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro ao atualizar medição"}), 500


@bp.route("/medicao-pasta/plano-acao", methods=["POST"])
@login_required
def medicao_pasta_plano_acao():
    from app.services import medicao_pasta_service
    data  = request.get_json(silent=True) or {}
    itens = data.get("itens") or []
    try:
        medicao_pasta_service.salvar_plano_acao(itens, current_user.id)
        return jsonify({"sucesso": True})
    except ValueError as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 400
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro ao salvar plano de ação"}), 500


# ─── Checklist ────────────────────────────────────────────────────────────────

@bp.route("/checklist/itens", methods=["GET"])
@login_required
def checklist_itens():
    from app.services import checklist_service
    return jsonify(checklist_service.list_itens())


@bp.route("/checklist/sessoes", methods=["GET"])
@login_required
def checklist_sessoes_list():
    from app.services import checklist_service
    data_sessao = request.args.get("data_sessao") or None
    setor = request.args.get("setor") or None
    linha = request.args.get("linha") or None
    limit = int(request.args.get("limit", "50") or "50")
    return jsonify(checklist_service.list_sessoes(data_sessao=data_sessao, setor=setor, linha=linha, limit=limit))


@bp.route("/checklist/sessoes", methods=["POST"])
@login_required
def checklist_sessoes_create():
    from app.services import checklist_service
    data = request.get_json(silent=True) or {}
    setor = (data.get("setor") or "").strip()
    linha = (data.get("linha") or "").strip()
    if not setor or not linha:
        return jsonify({"sucesso": False, "erro": "Setor e linha são obrigatórios"}), 400
    respostas = data.get("respostas") or []
    if not respostas:
        return jsonify({"sucesso": False, "erro": "Nenhuma resposta informada"}), 400
    try:
        sessao_data = {
            "setor": setor,
            "linha": linha,
            "modelo": data.get("modelo") or None,
            "mes": data.get("mes") or None,
            "responsavel": data.get("responsavel") or None,
            "data_sessao": data.get("data_sessao") or None,
        }
        sessao_id = checklist_service.create_session_with_respostas(sessao_data, respostas, current_user.id)
        return jsonify({"sucesso": True, "sessao_id": sessao_id})
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro ao salvar checklist"}), 500


@bp.route("/checklist/sessoes/<int:sessao_id>", methods=["GET"])
@login_required
def checklist_sessao_detail(sessao_id: int):
    from app.services import checklist_service
    detail = checklist_service.get_sessao_detail(sessao_id)
    if not detail:
        return jsonify({"sucesso": False, "erro": "Sessão não encontrada"}), 404
    return jsonify({"sucesso": True, "sessao": detail})


@bp.route("/checklist/plano-acao", methods=["POST"])
@login_required
def checklist_plano_acao_create():
    from app.services import checklist_service
    data = request.get_json(silent=True) or {}
    sessao_id = data.get("sessao_id")
    item_id = data.get("item_id")
    problema = (data.get("problema") or "").strip()
    if not sessao_id or not item_id or not problema:
        return jsonify({"sucesso": False, "erro": "Dados incompletos"}), 400
    try:
        checklist_service.create_plano_acao({
            "sessao_id": sessao_id,
            "item_id": item_id,
            "problema": problema,
            "causa": data.get("causa") or None,
            "acao": data.get("acao") or None,
            "quando": data.get("quando") or None,
            "responsavel": data.get("responsavel") or None,
            "status": data.get("status", "Aberto"),
        })
        return jsonify({"sucesso": True})
    except Exception:
        return jsonify({"sucesso": False, "erro": "Erro ao salvar plano de ação"}), 500
