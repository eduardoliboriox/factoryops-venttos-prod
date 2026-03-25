from datetime import date
from app.repositories import apontamento_repository as repo


def data_padrao() -> tuple[str, str]:
    hoje = str(date.today())
    return hoje, hoje


def listar_agrupado(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "") -> list:
    return repo.listar_agrupado(data_inicial, data_final, setor, linha, turno)


def ops_abertas() -> list:
    return repo.ops_abertas()


def vincular(data: str, turno: str, modelo: str, linha: str, op_id: int, quantidade: int) -> None:
    if not data or not turno or not modelo or not linha:
        raise ValueError("Dados do apontamento incompletos.")
    if not op_id or op_id <= 0:
        raise ValueError("OP inválida.")
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")
    repo.vincular(data, turno, modelo, linha, op_id, quantidade)


def desvincular(apontamento_id: int) -> None:
    if not apontamento_id or apontamento_id <= 0:
        raise ValueError("Apontamento inválido.")
    repo.desvincular(apontamento_id)
