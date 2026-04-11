import json
from app.repositories import resumo_producao_repository as repo

TURNOS_VALIDOS = {"1T", "2T", "3T"}
STATUS_VALIDOS = {"rascunho", "finalizado"}

TURNO_LABEL = {
    "1T": "1° Turno",
    "2T": "2° Turno",
    "3T": "3° Turno",
}


def _parse_ops_field(ops_raw) -> list:
    if not ops_raw:
        return []
    try:
        parsed = json.loads(ops_raw)
        if isinstance(parsed, list):
            return [
                {
                    "op": str(item.get("op", "")).upper(),
                    "quantidade": int(item.get("quantidade") or 0),
                }
                for item in parsed
                if str(item.get("op", "")).strip()
            ]
    except (ValueError, TypeError):
        pass
    return [
        {"op": op.strip().upper(), "quantidade": 0}
        for op in ops_raw.split("\n")
        if op.strip()
    ]


def listar(data_inicial: str = "", data_final: str = "", turno: str = "",
           status: str = "", criado_por: str = "") -> list:
    return repo.listar(data_inicial, data_final, turno, status, criado_por)


def buscar_por_id(resumo_id: int) -> dict | None:
    resumo = repo.buscar_por_id(resumo_id)
    if resumo:
        for linha in resumo.get("linhas", []):
            for modelo in linha.get("modelos", []):
                modelo["ops_items"] = _parse_ops_field(modelo.get("ops"))
    return resumo


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
        raise ValueError(f"Turno inválido. Use: {', '.join(sorted(TURNOS_VALIDOS))}.")

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

            ops_raw = modelo.get("ops")
            if isinstance(ops_raw, list):
                ops_clean = [
                    {
                        "op": str(item.get("op", "")).strip().upper(),
                        "quantidade": int(item.get("quantidade") or 0),
                    }
                    for item in ops_raw
                    if str(item.get("op", "")).strip()
                ]
                ops = json.dumps(ops_clean, ensure_ascii=False) if ops_clean else None
            else:
                ops = (ops_raw or "").strip() or None

            modelos.append({
                "codigo_modelo": codigo,
                "produto":       (modelo.get("produto") or "").strip() or None,
                "ops":           ops,
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
