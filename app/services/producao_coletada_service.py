import json
import threading
import uuid
from datetime import date, time
from flask import current_app
from app.repositories import producao_coletada_repository as repo
from app.repositories import turno_config_repository as tc_repo


_jobs: dict = {}

_TURNOS_NOTURNOS_FALLBACK: dict[str, tuple[time, time]] = {
    "2º Turno": (time(16, 48), time(2, 35)),
}


def _hora_params_turno_noturno(turno: str) -> tuple:
    if not turno:
        return None, None
    for c in tc_repo.listar():
        if c["turno"] == turno and c["hora_fim"] < c["hora_inicio"]:
            return c["hora_inicio"], c["hora_fim"]
    if turno in _TURNOS_NOTURNOS_FALLBACK:
        return _TURNOS_NOTURNOS_FALLBACK[turno]
    return None, None


def listar(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "") -> list:
    hora_ini, hora_fim = _hora_params_turno_noturno(turno)
    return repo.listar(data_inicial, data_final, setor, linha, turno,
                       hora_inicio_turno=hora_ini, hora_fim_turno=hora_fim)


def totais(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "") -> dict:
    hora_ini, hora_fim = _hora_params_turno_noturno(turno)
    return repo.totais(data_inicial, data_final, setor, linha, turno,
                       hora_inicio_turno=hora_ini, hora_fim_turno=hora_fim)


def filtros_disponiveis(setor: str = "") -> dict:
    return {
        "setores": repo.setores_disponiveis(),
        "linhas":  repo.linhas_disponiveis(setor),
    }


def data_padrao() -> tuple[str, str]:
    hoje = str(date.today())
    return hoje, hoje


def iniciar_importacao(conteudo_bytes: bytes) -> str:
    try:
        registros = json.loads(conteudo_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Arquivo inválido: {e}")

    if not isinstance(registros, list):
        raise ValueError("O arquivo deve conter uma lista JSON de registros.")

    if not registros:
        raise ValueError("O arquivo está vazio.")

    app = current_app._get_current_object()
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "total": len(registros), "salvos": 0, "erros": 0}

    t = threading.Thread(target=_executar_importacao, args=(app, job_id, registros), daemon=True)
    t.start()
    return job_id


def _executar_importacao(app, job_id: str, registros: list):
    BATCH = 1000
    total = len(registros)
    salvos = 0
    erros  = 0

    try:
        with app.app_context():
            for i in range(0, total, BATCH):
                resultado = repo.importar_registros(registros[i:i + BATCH])
                salvos += resultado["salvos"]
                erros  += resultado["erros"]
                _jobs[job_id].update(salvos=salvos, erros=erros)

        _jobs[job_id]["status"] = "done"

    except Exception as e:
        _jobs[job_id].update(status="error", mensagem=str(e))


def status_importacao(job_id: str) -> dict:
    return _jobs.get(job_id, {"status": "not_found"})
