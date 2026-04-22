from datetime import date
from app.repositories import entregas_repository as repo

STATUSES_PEDIDO = ["aberto", "em_producao", "pronto", "entregue"]

STATUSES_ENTREGA = ["aguardando_nf", "nf_emitida", "em_carregamento", "em_transito", "entregue"]

STATUS_LABEL = {
    "aberto":        "Aberto",
    "em_producao":   "Em Produção",
    "pronto":        "Pronto",
    "entregue":      "Entregue",
    "aguardando_nf": "Aguardando NF",
    "nf_emitida":    "NF Emitida",
    "em_carregamento": "Em Carregamento",
    "em_transito":   "Em Trânsito",
}

STATUS_COR = {
    "aberto":          "secondary",
    "em_producao":     "warning",
    "pronto":          "success",
    "entregue":        "dark",
    "aguardando_nf":   "secondary",
    "nf_emitida":      "info",
    "em_carregamento": "warning",
    "em_transito":     "primary",
}

PROGRESSO_ENTREGA = {
    "aguardando_nf":   10,
    "nf_emitida":      30,
    "em_carregamento": 55,
    "em_transito":     80,
    "entregue":        100,
}

PROXIMO_STATUS = {
    "aguardando_nf":   "nf_emitida",
    "nf_emitida":      "em_carregamento",
    "em_carregamento": "em_transito",
    "em_transito":     "entregue",
}


def data_padrao() -> str:
    return str(date.today())


def listar_pedidos(status: str = "", modelo: str = "", data_inicial: str = "", data_final: str = "") -> list:
    return repo.listar_pedidos(status, modelo, data_inicial, data_final)


def buscar_pedido(pedido_id: int) -> dict | None:
    return repo.buscar_pedido(pedido_id)


def criar_pedido(numero_pedido: str, cliente: str, modelo: str, familia: str,
                 quantidade: int, data_pedido: str, data_entrega: str, observacao: str) -> int:
    if not numero_pedido.strip() or not cliente.strip() or not modelo.strip():
        raise ValueError("Número do pedido, cliente e modelo são obrigatórios.")
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")
    if data_entrega < data_pedido:
        raise ValueError("Data de entrega não pode ser anterior à data do pedido.")
    return repo.criar_pedido(numero_pedido.strip(), cliente.strip(), modelo.strip(),
                             familia.strip() if familia else "", quantidade,
                             data_pedido, data_entrega, observacao)


def atualizar_pedido(pedido_id: int, numero_pedido: str, cliente: str, modelo: str, familia: str,
                     quantidade: int, data_pedido: str, data_entrega: str, observacao: str) -> None:
    if not repo.buscar_pedido(pedido_id):
        raise ValueError("Pedido não encontrado.")
    if not numero_pedido.strip() or not cliente.strip() or not modelo.strip():
        raise ValueError("Número do pedido, cliente e modelo são obrigatórios.")
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")
    repo.atualizar_pedido(pedido_id, numero_pedido.strip(), cliente.strip(), modelo.strip(),
                          familia.strip() if familia else "", quantidade,
                          data_pedido, data_entrega, observacao)


def excluir_pedido(pedido_id: int) -> None:
    if not repo.buscar_pedido(pedido_id):
        raise ValueError("Pedido não encontrado.")
    repo.excluir_pedido(pedido_id)


def listar_entregas() -> list:
    rows = repo.listar_entregas()
    for row in rows:
        row["progresso"] = PROGRESSO_ENTREGA.get(row["status"], 0)
        row["proximo_status"] = PROXIMO_STATUS.get(row["status"])
        row["proximo_label"] = STATUS_LABEL.get(row["proximo_status"], "") if row["proximo_status"] else ""
    return rows


def buscar_entrega(entrega_id: int) -> dict | None:
    return repo.buscar_entrega(entrega_id)


def listar_remessas_pedido(pedido_id: int) -> list:
    rows = repo.listar_remessas_pedido(pedido_id)
    for row in rows:
        row["status_label"] = STATUS_LABEL.get(row["status"], row["status"])
        row["status_cor"] = STATUS_COR.get(row["status"], "secondary")
    return rows


def criar_entrega(pedido_id: int, quantidade: int, nota_fiscal: str = "") -> int:
    pedido = repo.buscar_pedido(pedido_id)
    if not pedido:
        raise ValueError("Pedido não encontrado.")
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")
    qtd_ja_em_remessa = repo.soma_remessas_pedido(pedido_id)
    disponivel = pedido["quantidade"] - qtd_ja_em_remessa
    if quantidade > disponivel:
        raise ValueError(
            f"Quantidade ({quantidade}) supera o saldo disponível para remessa ({disponivel})."
        )
    return repo.criar_entrega(pedido_id, quantidade, nota_fiscal)


def atualizar_status_entrega(entrega_id: int, status: str,
                              nota_fiscal: str | None = None,
                              motorista_id: int | None = None) -> None:
    if status not in STATUSES_ENTREGA:
        raise ValueError(f"Status inválido: {status}.")
    repo.atualizar_status_entrega(entrega_id, status, nota_fiscal, motorista_id)


def sincronizar_equipe_entrega(entrega_id: int, membro_ids: list[int]) -> None:
    repo.sincronizar_equipe_entrega(entrega_id, membro_ids)


def atualizar_localizacao(entrega_id: int, lat: float, lng: float) -> None:
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        raise ValueError("Coordenadas inválidas.")
    repo.atualizar_localizacao(entrega_id, lat, lng)


def listar_equipe(tipo: str = "") -> list:
    return repo.listar_equipe(tipo)


def criar_membro_equipe(nome: str, tipo: str, telefone: str) -> int:
    if not nome.strip():
        raise ValueError("Nome é obrigatório.")
    if tipo not in ("motorista", "apoio"):
        raise ValueError("Tipo deve ser 'motorista' ou 'apoio'.")
    return repo.criar_membro_equipe(nome.strip(), tipo, telefone.strip() if telefone else "")


def desativar_membro_equipe(membro_id: int) -> None:
    repo.desativar_membro_equipe(membro_id)


def resumo_apontamento_logistica(data: str) -> list:
    return repo.resumo_apontamento_logistica(data)
