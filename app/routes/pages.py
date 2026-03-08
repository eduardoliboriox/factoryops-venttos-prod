from flask import Blueprint, render_template
from flask_login import login_required
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
    return render_template("modelos.html", active_menu="smt_modelos")


@bp.route("/smt/cadastro")
@login_required
def smt_cadastro():
    return render_template("cadastro.html", active_menu="smt_cadastro")


@bp.route("/smt/calcular")
@login_required
def smt_calcular():
    return render_template("calcular.html", active_menu="smt_calcular")


@bp.route("/smt/estudo-tempo")
@login_required
def smt_estudo_tempo():
    return render_template("estudo_tempo.html", active_menu="smt_estudo_tempo")


@bp.route("/smt/mais")
@login_required
def smt_mais():
    """
    Página "Mais" (prioridade mobile):
    - reduz itens no bottom-nav
    - exibe módulos extras em cards (Cálculos, Estudo de Tempo)
    """
    return render_template("mais.html", active_menu="smt_more")


@bp.route("/smt/estudo-tempo/print/<int:study_id>")
@login_required
def smt_estudo_tempo_print(study_id: int):
    detail = time_studies_service.get_study_detail(study_id)
    if not detail:
        # mantém simples (sem nova página de erro)
        return render_template(
            "estudo_tempo_print.html",
            active_menu="smt_estudo_tempo",
            study=None,
            operations=[],
            totals={},
            not_found=True,
        )

    return render_template(
        "estudo_tempo_print.html",
        active_menu="smt_estudo_tempo",
        study=detail.get("study"),
        operations=detail.get("operations") or [],
        totals=detail.get("totals") or {},
        not_found=False,
    )


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
