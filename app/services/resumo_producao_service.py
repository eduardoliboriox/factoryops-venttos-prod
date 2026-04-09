import json
from app.repositories import resumo_producao_repository as repo

TURNOS_VALIDOS = {"1T", "2T", "3T"}
STATUS_VALIDOS = {"rascunho", "finalizado"}


def listar(data_inicial: str = "", data_final: str = "", turno: str = "", status: str = "") -> list:
    return repo.listar(data_inicial, data_final, turno, status)


def buscar_por_id(resumo_id: int) -> dict | None:
    return repo.buscar_por_id(resumo_id)


def _parsear_dados_json(form_data: dict) -> dict:
    raw = form_data.get("dados_json", "")
    try:
        payload = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, TypeError):
        raise ValueError("Dados do formulário inválidos.")

    data  = form_data.get("data", "").strip()
    turno = form_data.get("turno", "").strip()

    if not data:
        raise ValueError("Data é obrigatória.")
    if turno not in TURNOS_VALIDOS:
        raise ValueError(f"Turno inválido. Use: {', '.join(TURNOS_VALIDOS)}.")

    status = form_data.get("status", "rascunho").strip()
    if status not in STATUS_VALIDOS:
        status = "rascunho"

    linhas = []
    for linha in payload.get("linhas", []):
        nome = (linha.get("nome_linha") or "").strip()
        if not nome:
            continue

        modelos = []
        for modelo in linha.get("modelos", []):
            codigo = (modelo.get("codigo_modelo") or "").strip()
            if not codigo:
                continue

            try:
                top = int(modelo.get("produzido_top") or 0)
            except (ValueError, TypeError):
                top = 0

            try:
                bot = int(modelo.get("produzido_bot") or 0)
            except (ValueError, TypeError):
                bot = 0

            modelos.append({
                "codigo_modelo": codigo,
                "produto":       (modelo.get("produto") or "").strip() or None,
                "ops":           (modelo.get("ops") or "").strip() or None,
                "produzido_top": top,
                "produzido_bot": bot,
                "observacao":    (modelo.get("observacao") or "").strip() or None,
            })

        linhas.append({
            "nome_linha": nome,
            "observacao": (linha.get("observacao") or "").strip() or None,
            "modelos":    modelos,
        })

    return {
        "data":   data,
        "turno":  turno,
        "status": status,
        "linhas": linhas,
    }


def criar(form_data: dict, username: str) -> int:
    data = _parsear_dados_json(form_data)
    data["criado_por"] = username
    return repo.inserir(data)


def atualizar(resumo_id: int, form_data: dict) -> None:
    if not resumo_id or resumo_id <= 0:
        raise ValueError("Relatório inválido.")
    data = _parsear_dados_json(form_data)
    repo.atualizar(resumo_id, data)


def excluir(resumo_id: int) -> None:
    if not resumo_id or resumo_id <= 0:
        raise ValueError("Relatório inválido.")
    repo.excluir(resumo_id)
