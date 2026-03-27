from app.repositories import turno_config_repository as repo

TURNOS_VALIDOS = ["1º Turno", "2º Turno", "3º Turno"]


def listar_por_turno() -> dict:
    registros = repo.listar()
    agrupado = {t: [] for t in TURNOS_VALIDOS}
    for r in registros:
        turno = r["turno"]
        if turno in agrupado:
            agrupado[turno].append(r)
    return agrupado


def adicionar(turno: str, hora_inicio: str, hora_fim: str) -> None:
    if turno not in TURNOS_VALIDOS:
        raise ValueError(f"Turno inválido: {turno}")
    if not hora_inicio or not hora_fim:
        raise ValueError("Horários não podem ser vazios.")
    ordem = repo.proximo_ordem(turno)
    repo.inserir(turno, hora_inicio, hora_fim, ordem)


def excluir(id: int) -> None:
    repo.excluir(id)
