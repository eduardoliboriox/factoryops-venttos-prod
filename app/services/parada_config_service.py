from app.repositories import parada_config_repository as repo
from app.repositories import linha_config_repository as lc_repo

TIPOS_VALIDOS = ["INTERVALO_1", "INTERVALO_2", "GINASTICA", "DDS", "REFEICAO", "SETUP", "SMD_5S", "OUTROS"]
TURNOS_VALIDOS = ["1º Turno", "2º Turno", "3º Turno"]
DIAS_SEMANA = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]


def listar_por_setor() -> dict:
    registros = repo.listar()
    agrupado: dict = {}
    for r in registros:
        chave = r["setor"] or "Geral"
        agrupado.setdefault(chave, []).append(r)
    return agrupado


def adicionar(form_data: dict) -> None:
    tipo = form_data.get("tipo", "").strip().upper()

    if tipo not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo inválido: {tipo}")

    try:
        duracao_min = int(form_data.get("duracao_min", 0))
    except (ValueError, TypeError):
        raise ValueError("Duração deve ser um número inteiro.")

    if duracao_min < 0:
        raise ValueError("Duração não pode ser negativa.")

    turno = form_data.get("turno", "").strip() or None
    if turno and turno not in TURNOS_VALIDOS:
        raise ValueError(f"Turno inválido: {turno}")

    dias_selecionados = form_data.getlist("frequencia_dias") if hasattr(form_data, "getlist") else []
    dias_validos = [d for d in dias_selecionados if d in DIAS_SEMANA]
    frequencia_dias = ",".join(dias_validos) if dias_validos else None

    hora_inicio = form_data.get("hora_inicio", "").strip() or None

    repo.inserir({
        "setor":          form_data.get("setor", "").strip() or None,
        "linha":          form_data.get("linha", "").strip() or None,
        "tipo":           tipo,
        "turno":          turno,
        "hora_inicio":    hora_inicio,
        "duracao_min":    duracao_min,
        "frequencia_dias": frequencia_dias,
    })


def excluir(parada_id: int) -> None:
    if not parada_id or parada_id <= 0:
        raise ValueError("ID inválido.")
    repo.excluir(parada_id)


def opcoes_linha() -> dict:
    agrupado = lc_repo.listar_por_setor()
    return {setor: [r["linha"] for r in rows] for setor, rows in agrupado.items()}
