import json
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


def importar_de_arquivo(conteudo_bytes: bytes) -> dict:
    try:
        registros = json.loads(conteudo_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Arquivo inválido: {e}")

    if not isinstance(registros, list):
        raise ValueError("O arquivo deve conter uma lista JSON de registros.")

    if not registros:
        raise ValueError("O arquivo está vazio.")

    return repo.importar_registros(registros)
