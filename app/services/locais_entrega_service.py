from app.repositories import locais_entrega_repository as repo


def listar_locais(cliente: str = "") -> list:
    return repo.listar_locais(cliente)


def criar_local(cliente: str, nome_local: str, endereco: str,
                lat: float | None, lng: float | None) -> int:
    if not cliente.strip():
        raise ValueError("Cliente é obrigatório.")
    if not nome_local.strip():
        raise ValueError("Nome do local é obrigatório.")
    return repo.criar_local(
        cliente.strip(), nome_local.strip(),
        endereco.strip() if endereco else "", lat, lng
    )


def atualizar_local(local_id: int, cliente: str, nome_local: str, endereco: str,
                    lat: float | None, lng: float | None) -> None:
    if not repo.buscar_local(local_id):
        raise ValueError("Local não encontrado.")
    if not cliente.strip() or not nome_local.strip():
        raise ValueError("Cliente e nome do local são obrigatórios.")
    repo.atualizar_local(
        local_id, cliente.strip(), nome_local.strip(),
        endereco.strip() if endereco else "", lat, lng
    )


def excluir_local(local_id: int) -> None:
    if not repo.buscar_local(local_id):
        raise ValueError("Local não encontrado.")
    repo.excluir_local(local_id)
