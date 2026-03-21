from datetime import date
from app.repositories import producao_coletada_repository as repo


def listar(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "") -> list:
    return repo.listar(data_inicial, data_final, setor, linha, turno)


def totais(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "") -> dict:
    return repo.totais(data_inicial, data_final, setor, linha, turno)


def filtros_disponiveis() -> dict:
    return {
        "setores": repo.setores_disponiveis(),
        "linhas":  repo.linhas_disponiveis(),
    }


def data_padrao() -> tuple[str, str]:
    hoje = str(date.today())
    return hoje, hoje
