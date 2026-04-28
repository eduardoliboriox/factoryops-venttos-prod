from app.repositories import linha_config_repository as repo

SETORES_VTE = ["PTH", "SMD", "IM", "PA"]
SETORES_VTT = ["PTH", "SMD", "IM", "PA"]
FILIAIS: dict[str, list[str]] = {"VTE": SETORES_VTE, "VTT": SETORES_VTT}


def listar_por_setor() -> dict:
    configurado = repo.listar_por_filial_setor()
    return {
        "VTE": {s: configurado.get("VTE", {}).get(s, []) for s in SETORES_VTE},
        "VTT": {s: configurado.get("VTT", {}).get(s, []) for s in SETORES_VTT},
    }


def listar_linhas_producao() -> list:
    return repo.listar_linhas_producao()


def atribuir(filial: str, setor: str, linha: str) -> int:
    if filial not in FILIAIS:
        raise ValueError(f"Filial inválida: {filial}")
    if setor not in FILIAIS[filial]:
        raise ValueError(f"Setor inválido para {filial}: {setor}")
    if not linha or not linha.strip():
        raise ValueError("Nome da linha não pode ser vazio.")
    return repo.atribuir(filial, setor, linha.strip())


def remover(id: int) -> None:
    repo.remover(id)
