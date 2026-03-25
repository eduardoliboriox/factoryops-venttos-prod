from app.repositories import controle_ops_repository as repo


def listar(filial: str = "", status: str = "") -> list:
    return repo.listar(filial, status)


def cadastrar(form_data: dict) -> None:
    numero_op = form_data.get("numero_op", "").strip()
    filial    = form_data.get("filial", "").strip()
    produto   = form_data.get("produto", "").strip()

    if not numero_op:
        raise ValueError("Número da OP é obrigatório.")
    if not filial:
        raise ValueError("Filial é obrigatória.")
    if not produto:
        raise ValueError("Produto é obrigatório.")

    try:
        quantidade = int(form_data.get("quantidade", "0"))
    except (ValueError, TypeError):
        raise ValueError("Quantidade deve ser um número inteiro.")

    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")

    repo.inserir({
        "filial":             filial,
        "numero_op":          numero_op,
        "produto":            produto,
        "descricao":          form_data.get("descricao", "").strip() or None,
        "armazem":            form_data.get("armazem", "").strip() or None,
        "quantidade":         quantidade,
        "pedido_venda":       form_data.get("pedido_venda", "").strip() or None,
        "item_pedido_venda":  form_data.get("item_pedido_venda", "").strip() or None,
    })


def filiais_disponiveis() -> list:
    return repo.filiais_disponiveis()
