import datetime
from app.repositories import checklist_linha_repository


def _serialize(value):
    if isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
        return value.isoformat()
    return value


def _serialize_row(row: dict) -> dict:
    return {k: _serialize(v) for k, v in row.items()}


def criar_registro(data: dict, user_id: int) -> dict:
    if not data.get("mes"):
        raise ValueError("Mês é obrigatório")
    if not data.get("setor"):
        raise ValueError("Setor é obrigatório")
    if not data.get("linha"):
        raise ValueError("Linha é obrigatória")

    registro = checklist_linha_repository.create_registro(data, user_id)
    registro_id = registro["id"]

    if data.get("entradas"):
        checklist_linha_repository.upsert_entradas(registro_id, data["entradas"])
    if data.get("assinaturas"):
        checklist_linha_repository.upsert_assinaturas(registro_id, data["assinaturas"])

    return _serialize_row(registro)


def atualizar_registro(registro_id: int, data: dict) -> dict:
    registro = checklist_linha_repository.update_registro(registro_id, data)
    if not registro:
        raise ValueError("Registro não encontrado")

    checklist_linha_repository.upsert_entradas(registro_id, data.get("entradas") or [])
    checklist_linha_repository.upsert_assinaturas(registro_id, data.get("assinaturas") or [])

    return _serialize_row(registro)


def buscar_registro(registro_id: int) -> dict | None:
    result = checklist_linha_repository.get_registro_by_id(registro_id)
    if not result:
        return None

    entradas    = [_serialize_row(e) for e in result.pop("entradas", [])]
    assinaturas = [_serialize_row(a) for a in result.pop("assinaturas", [])]
    return {**_serialize_row(result), "entradas": entradas, "assinaturas": assinaturas}


def salvar_plano_acao(registro_id: int, itens: list, user_id: int):
    checklist_linha_repository.upsert_plano_acao(registro_id, itens, user_id)


def buscar_plano_acao(registro_id: int) -> list:
    rows = checklist_linha_repository.get_plano_by_registro_id(registro_id)
    return [_serialize_row(r) for r in rows]


def listar_registros(mes=None, ano=None, setor=None, linha=None) -> list:
    rows = checklist_linha_repository.list_registros(mes=mes, ano=ano, setor=setor, linha=linha)
    return [_serialize_row(r) for r in rows]
