from app.repositories import roteiro_repository as repo

_SETORES_VALIDOS = {"SMD", "PTH", "IM", "PA", "VTT"}


def listar(cliente: str = "") -> list:
    return repo.listar(cliente)


def clientes_roteiros() -> list:
    return repo.listar_clientes()


def clientes_modelos() -> list:
    return repo.listar_clientes_modelos()


def codigos_por_cliente(cliente: str) -> list:
    if not cliente:
        return []
    return repo.listar_codigos_por_cliente(cliente)


def buscar(roteiro_id: int) -> dict:
    roteiro = repo.buscar_por_id(roteiro_id)
    if not roteiro:
        raise ValueError("Roteiro não encontrado.")
    return roteiro


def modelos_do_roteiro(roteiro_id: int) -> list:
    return repo.modelos_do_roteiro(roteiro_id)


def criar(dados: dict) -> int:
    _validar(dados)
    return repo.inserir(dados)


def editar(roteiro_id: int, dados: dict) -> None:
    if roteiro_id <= 0:
        raise ValueError("Roteiro inválido.")
    _validar(dados)
    repo.atualizar(roteiro_id, dados)


def excluir(roteiro_id: int) -> None:
    if roteiro_id <= 0:
        raise ValueError("Roteiro inválido.")
    repo.excluir(roteiro_id)


def vincular_modelo(roteiro_id: int, modelo_codigo: str) -> None:
    if roteiro_id <= 0:
        raise ValueError("Roteiro inválido.")
    codigo = (modelo_codigo or "").strip().upper()
    if not codigo:
        raise ValueError("Código do modelo é obrigatório.")
    repo.vincular_modelo(roteiro_id, codigo)


def desvincular_modelo(roteiro_id: int, modelo_codigo: str) -> None:
    if roteiro_id <= 0:
        raise ValueError("Roteiro inválido.")
    codigo = (modelo_codigo or "").strip().upper()
    if not codigo:
        raise ValueError("Código do modelo é obrigatório.")
    repo.desvincular_modelo(roteiro_id, codigo)


def _validar(dados: dict) -> None:
    nome = (dados.get("nome") or "").strip()
    cliente = (dados.get("cliente") or "").strip()

    if not nome:
        raise ValueError("Nome do roteiro é obrigatório.")
    if not cliente:
        raise ValueError("Cliente é obrigatório.")

    etapas = dados.get("etapas") or []
    setores_vistos = set()
    for etapa in etapas:
        setor = (etapa.get("setor") or "").strip().upper()
        if not setor:
            continue
        if setor in setores_vistos:
            raise ValueError(f"Setor duplicado na lista de etapas: {setor}.")
        setores_vistos.add(setor)
