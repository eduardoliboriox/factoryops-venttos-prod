import datetime
from app.repositories import medicao_pasta_repository


def _serialize(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


def _serialize_row(row: dict) -> dict:
    return {k: _serialize(v) for k, v in row.items()}


def criar_registro(data: dict, user_id: int) -> dict:
    if not data.get("data"):
        raise ValueError("Data é obrigatória")
    if not data.get("linha"):
        raise ValueError("Linha é obrigatória")

    registro = medicao_pasta_repository.create_registro(data, user_id)
    registro_id = registro["id"]

    if data.get("medicoes"):
        medicao_pasta_repository.upsert_medicoes(registro_id, data["medicoes"])
    if data.get("assinaturas"):
        medicao_pasta_repository.upsert_assinaturas(registro_id, data["assinaturas"])

    return _serialize_row(registro)


def atualizar_registro(registro_id: int, data: dict) -> dict:
    registro = medicao_pasta_repository.update_registro(registro_id, data)
    if not registro:
        raise ValueError("Registro não encontrado")

    medicao_pasta_repository.upsert_medicoes(registro_id, data.get("medicoes") or [])
    medicao_pasta_repository.upsert_assinaturas(registro_id, data.get("assinaturas") or [])

    return _serialize_row(registro)


def buscar_registro(registro_id: int) -> dict | None:
    result = medicao_pasta_repository.get_registro_by_id(registro_id)
    if not result:
        return None

    medicoes    = [_serialize_row(m) for m in result.pop("medicoes", [])]
    assinaturas = [_serialize_row(a) for a in result.pop("assinaturas", [])]

    return {**_serialize_row(result), "medicoes": medicoes, "assinaturas": assinaturas}


def listar_registros(data=None, setor=None, linha=None) -> list:
    rows = medicao_pasta_repository.list_registros(data=data, setor=setor, linha=linha)
    return [_serialize_row(r) for r in rows]


def salvar_plano_acao(itens: list, user_id: int, registro_id: int | None = None):
    if not itens:
        raise ValueError("Nenhum item informado")
    medicao_pasta_repository.create_plano_acao_itens(itens, user_id, registro_id)


def buscar_plano_por_registro(registro_id: int) -> list:
    rows = medicao_pasta_repository.get_plano_by_registro_id(registro_id)
    return [_serialize_row(r) for r in rows]
