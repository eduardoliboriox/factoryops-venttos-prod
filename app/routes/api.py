from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.services import modelos_service
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
    """
    Retorna histórico filtrado corretamente por:
    - codigo
    - fase (TOP/BOTTOM)
    - linha (SMD-xx)
    """
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
