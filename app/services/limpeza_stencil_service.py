import datetime
from app.repositories import limpeza_stencil_repository


def _serialize(value):
    if isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
        return value.isoformat()
    return value


def _serialize_row(row: dict) -> dict:
    return {k: _serialize(v) for k, v in row.items()}


def criar_registro(data: dict, user_id: int) -> dict:
    if not data.get("data"):
        raise ValueError("Data é obrigatória")
    if not data.get("linha"):
        raise ValueError("Linha é obrigatória")

    registro = limpeza_stencil_repository.create_registro(data, user_id)
    registro_id = registro["id"]

    if data.get("horarios"):
        limpeza_stencil_repository.upsert_horarios(registro_id, data["horarios"])
    if data.get("assinaturas"):
        limpeza_stencil_repository.upsert_assinaturas(registro_id, data["assinaturas"])

    return _serialize_row(registro)


def atualizar_registro(registro_id: int, data: dict) -> dict:
    registro = limpeza_stencil_repository.update_registro(registro_id, data)
    if not registro:
        raise ValueError("Registro não encontrado")

    limpeza_stencil_repository.upsert_horarios(registro_id, data.get("horarios") or [])
    limpeza_stencil_repository.upsert_assinaturas(registro_id, data.get("assinaturas") or [])

    return _serialize_row(registro)


def buscar_registro(registro_id: int) -> dict | None:
    result = limpeza_stencil_repository.get_registro_by_id(registro_id)
    if not result:
        return None

    horarios    = [_serialize_row(h) for h in result.pop("horarios", [])]
    assinaturas = [_serialize_row(a) for a in result.pop("assinaturas", [])]

    return {**_serialize_row(result), "horarios": horarios, "assinaturas": assinaturas}


def listar_registros(data=None, setor=None, linha=None) -> list:
    rows = limpeza_stencil_repository.list_registros(data=data, setor=setor, linha=linha)
    return [_serialize_row(r) for r in rows]
