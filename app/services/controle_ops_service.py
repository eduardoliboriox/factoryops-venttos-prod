import re
from app.repositories import controle_ops_repository as repo

ROTEIRO_PADRAO = [
    ("PTH", "01"),
    ("SMD", "02"),
    ("IM",  "03"),
]

FASES_VALIDAS = {"TOP", "BOTTOM", "AMBAS"}

_OP_RE_INDIVIDUAL = re.compile(r'^[A-Za-z]{5}\d{6}$|^[A-Za-z]{6}\d{5}$')
_OP_RE_BASE       = re.compile(r'^[A-Za-z]{5}\d{4}$|^[A-Za-z]{6}\d{3}$')
_OP_SUFIXOS_VALIDOS = {"01", "02", "03", "04"}


def listar(filial: str = "", status: str = "", setor: str = "") -> list:
    return repo.listar(filial, status, setor)


def buscar_por_id(op_id: int) -> dict | None:
    return repo.buscar_por_id(op_id)


def _validar_e_montar(form_data: dict, roteiro_padrao: bool = False) -> dict:
    numero_op   = form_data.get("numero_op", "").strip()
    filial      = form_data.get("filial", "").strip()
    produto     = form_data.get("produto", "").strip()
    setor       = form_data.get("setor", "").strip() or None
    fase_modelo = form_data.get("fase_modelo", "").strip() or None

    if not numero_op:
        raise ValueError("Número da OP é obrigatório.")

    if roteiro_padrao:
        if not _OP_RE_BASE.match(numero_op):
            raise ValueError(
                "Para Roteiro Padrão, informe a base da OP sem sufixo: "
                "5 letras + 4 números ou 6 letras + 3 números."
            )
    else:
        if not _OP_RE_INDIVIDUAL.match(numero_op):
            raise ValueError(
                "Formato da OP inválido. Use 5 letras + 6 números ou 6 letras + 5 números."
            )
        if numero_op[-2:] not in _OP_SUFIXOS_VALIDOS:
            raise ValueError(
                "O sufixo da OP deve terminar em 01, 02, 03 ou 04 (referência ao setor)."
            )

    if not filial:
        raise ValueError("Filial é obrigatória.")
    if not produto:
        raise ValueError("Produto é obrigatório.")
    if fase_modelo and fase_modelo not in FASES_VALIDAS:
        raise ValueError(f"Fase inválida: {fase_modelo}.")

    try:
        quantidade = int(form_data.get("quantidade", "0"))
    except (ValueError, TypeError):
        raise ValueError("Quantidade deve ser um número inteiro.")

    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")

    return {
        "numero_op":         numero_op,
        "filial":            filial,
        "produto":           produto,
        "setor":             setor,
        "fase_modelo":       fase_modelo,
        "descricao":         form_data.get("descricao", "").strip() or None,
        "armazem":           form_data.get("armazem", "").strip() or None,
        "quantidade":        quantidade,
        "pedido_venda":      form_data.get("pedido_venda", "").strip() or None,
        "item_pedido_venda": form_data.get("item_pedido_venda", "").strip() or None,
    }


def cadastrar(form_data: dict) -> None:
    roteiro = form_data.get("roteiro_padrao") == "1"
    data = _validar_e_montar(form_data, roteiro_padrao=roteiro)

    if roteiro:
        registros = [
            {**data, "numero_op": data["numero_op"] + sufixo, "setor": s}
            for s, sufixo in ROTEIRO_PADRAO
        ]
        repo.inserir_lote(registros)
    else:
        repo.inserir(data)


def atualizar(op_id: int, form_data: dict) -> None:
    data = _validar_e_montar(form_data)
    repo.atualizar(op_id, data)


def excluir(op_id: int) -> None:
    if not op_id or op_id <= 0:
        raise ValueError("OP inválida.")
    repo.excluir(op_id)


def filiais_disponiveis() -> list:
    return repo.filiais_disponiveis()
