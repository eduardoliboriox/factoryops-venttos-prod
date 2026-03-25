import json
import threading
import uuid
from datetime import date
from flask import current_app
from app.repositories import producao_coletada_repository as repo


_jobs: dict = {}


def listar(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "") -> list:
    return repo.listar(data_inicial, data_final, setor, linha, turno)


def totais(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "") -> dict:
    return repo.totais(data_inicial, data_final, setor, linha, turno)


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
