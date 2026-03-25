from app.repositories import controle_ops_repository as repo

ROTEIRO_PADRAO = [
    ("PTH", "01"),
    ("IM",  "02"),
    ("SMD", "03"),
]


def listar(filial: str = "", status: str = "", setor: str = "") -> list:
    return repo.listar(filial, status, setor)


def cadastrar(form_data: dict) -> None:
    numero_op = form_data.get("numero_op", "").strip()
    filial    = form_data.get("filial", "").strip()
    produto   = form_data.get("produto", "").strip()
    setor     = form_data.get("setor", "").strip() or None

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

    base = {
        "filial":            filial,
        "produto":           produto,
        "descricao":         form_data.get("descricao", "").strip() or None,
        "armazem":           form_data.get("armazem", "").strip() or None,
        "quantidade":        quantidade,
        "pedido_venda":      form_data.get("pedido_venda", "").strip() or None,
        "item_pedido_venda": form_data.get("item_pedido_venda", "").strip() or None,
    }

    if form_data.get("roteiro_padrao") == "1":
        registros = [
            {**base, "numero_op": numero_op + sufixo, "setor": s}
            for s, sufixo in ROTEIRO_PADRAO
        ]
        repo.inserir_lote(registros)
    else:
        repo.inserir({**base, "numero_op": numero_op, "setor": setor})


def filiais_disponiveis() -> list:
    return repo.filiais_disponiveis()
