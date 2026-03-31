from app.repositories import linha_config_repository as repo

SETORES = ["PTH", "SMD", "IM", "PA", "VTT"]


def listar_por_setor() -> dict:
    configurado = repo.listar_por_setor()
    return {s: configurado.get(s, []) for s in SETORES}


def listar_linhas_producao() -> list:
    return repo.listar_linhas_producao()


def atribuir(setor: str, linha: str) -> None:
    if setor not in SETORES:
        raise ValueError(f"Setor inválido: {setor}")
    if not linha or not linha.strip():
        raise ValueError("Nome da linha não pode ser vazio.")
    repo.atribuir(setor, linha.strip())


def remover(id: int) -> None:
    repo.remover(id)
