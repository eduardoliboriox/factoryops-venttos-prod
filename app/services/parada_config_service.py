from app.repositories import parada_config_repository as repo
from app.repositories import linha_config_repository as lc_repo

TIPOS_VALIDOS = ["INTERVALO", "GINASTICA", "DDS", "ALMOCO", "SETUP", "OUTROS"]


def listar_por_setor() -> dict:
    registros = repo.listar()
    agrupado: dict = {}
    for r in registros:
        chave = r["setor"] or "Geral"
        agrupado.setdefault(chave, []).append(r)
    return agrupado


def adicionar(form_data: dict) -> None:
    tipo = form_data.get("tipo", "").strip().upper()
    nome = form_data.get("nome", "").strip()

    if not nome:
        raise ValueError("Nome da parada é obrigatório.")
    if tipo not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo inválido: {tipo}")

    try:
        duracao_min = int(form_data.get("duracao_min", 0))
    except (ValueError, TypeError):
        raise ValueError("Duração deve ser um número inteiro.")

    if duracao_min < 0:
        raise ValueError("Duração não pode ser negativa.")

    hora_inicio = form_data.get("hora_inicio", "").strip() or None

    repo.inserir({
        "setor":       form_data.get("setor", "").strip() or None,
        "linha":       form_data.get("linha", "").strip() or None,
        "tipo":        tipo,
        "nome":        nome,
        "hora_inicio": hora_inicio,
        "duracao_min": duracao_min,
    })


def excluir(parada_id: int) -> None:
    if not parada_id or parada_id <= 0:
        raise ValueError("ID inválido.")
    repo.excluir(parada_id)


def opcoes_linha() -> dict:
    registros = lc_repo.listar()
    setores: dict = {}
    for r in registros:
        setores.setdefault(r["setor"], []).append(r["linha"])
    return setores
