from datetime import date
from app.repositories import apontamento_repository as repo

SETORES_SMD = {"SMD"}


def data_padrao() -> tuple[str, str]:
    hoje = str(date.today())
    return hoje, hoje


def listar_agrupado(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "") -> list:
    return repo.listar_agrupado(data_inicial, data_final, setor, linha, turno)


def ops_abertas(setor: str = "") -> list:
    return repo.ops_abertas(setor)


def vincular(data: str, turno: str, modelo: str, linha: str, op_id: int, quantidade: int,
             setor: str = "", fase: str = None, lote: str = None) -> None:
    if not data or not turno or not modelo or not linha:
        raise ValueError("Dados do apontamento incompletos.")
    if not op_id or op_id <= 0:
        raise ValueError("OP inválida.")
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")

    fase_norm = fase.strip().upper() if fase and fase.strip() else None

    if setor in SETORES_SMD and fase_norm not in ("TOP", "BOTTOM"):
        raise ValueError("Para SMD informe a fase: TOP ou BOTTOM.")
    if setor not in SETORES_SMD:
        fase_norm = None

    repo.vincular(data, turno, modelo, linha, op_id, quantidade, fase_norm, lote or None)


def desvincular(apontamento_id: int) -> None:
    if not apontamento_id or apontamento_id <= 0:
        raise ValueError("Apontamento inválido.")
    repo.desvincular(apontamento_id)


_ORDEM_SETORES = ["PTH", "IM", "SMD", "PA", "VTT"]


def fila_producao() -> dict:
    rows = repo.fila_producao()
    agrupado: dict = {}
    for row in rows:
        setor = row["setor"] or "Sem setor"
        agrupado.setdefault(setor, []).append(dict(row))
    resultado: dict = {}
    for s in _ORDEM_SETORES:
        if s in agrupado:
            resultado[s] = agrupado[s]
    for s in agrupado:
        if s not in resultado:
            resultado[s] = agrupado[s]
    return resultado
