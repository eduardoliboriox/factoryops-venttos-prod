from __future__ import annotations
from datetime import datetime, timedelta, time

from app.repositories import planejamento_repository as repo
from app.repositories import linha_config_repository as lc_repo

TURNOS_VALIDOS  = ["1º Turno", "2º Turno", "3º Turno"]
STATUS_VALIDOS  = {"PLANEJADO", "EM_EXECUCAO", "CONCLUIDO", "CANCELADO"}


# ─── helpers de tempo ─────────────────────────────────────────────────────────

def _to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _from_minutes(m: int) -> time:
    m = m % (24 * 60)
    return time(m // 60, m % 60)


def _intervalo_minutos(inicio: time, fim: time) -> int:
    """Minutos de início a fim, cruzando meia-noite se necessário."""
    s = _to_minutes(inicio)
    e = _to_minutes(fim)
    if e <= s:
        e += 24 * 60
    return e - s


def _overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    """Sobreposição em minutos entre dois intervalos lineares."""
    return max(0, min(a_end, b_end) - max(a_start, b_start))


# ─── cálculo de hora_fim ──────────────────────────────────────────────────────

def calcular_hora_fim(
    hora_inicio: time,
    quantidade_planejada: int,
    taxa_horaria: int,
    turno: str,
    setor: str,
    linha: str,
) -> time | None:
    if taxa_horaria <= 0 or quantidade_planejada <= 0:
        return None

    minutos_necessarios = (quantidade_planejada / taxa_horaria) * 60

    intervalos = repo.turno_intervalos(turno)
    if not intervalos:
        return None

    paradas = repo.paradas_da_linha(setor, linha)
    paradas_min = [
        (_to_minutes(p["hora_inicio"]),
         _to_minutes(p["hora_inicio"]) + p["duracao_min"])
        for p in paradas
    ]

    minutos_restantes = minutos_necessarios
    cursor_min = _to_minutes(hora_inicio)

    for iv in intervalos:
        iv_start = _to_minutes(iv["hora_inicio"])
        iv_end   = _to_minutes(iv["hora_fim"])
        if iv_end <= iv_start:
            iv_end += 24 * 60

        janela_start = max(cursor_min, iv_start)
        if janela_start >= iv_end:
            continue

        brutos = iv_end - janela_start

        paradas_na_janela = sum(
            _overlap(janela_start, iv_end, p_s, p_e)
            for p_s, p_e in paradas_min
        )
        uteis = max(0, brutos - paradas_na_janela)

        if uteis <= 0:
            cursor_min = iv_end
            continue

        if uteis >= minutos_restantes:
            fim_min = janela_start + minutos_restantes + paradas_na_janela * (minutos_restantes / uteis)
            return _from_minutes(int(fim_min))
        else:
            minutos_restantes -= uteis
            cursor_min = iv_end

    return None


# ─── validação ────────────────────────────────────────────────────────────────

def _validar_e_montar(form_data: dict) -> dict:
    data    = form_data.get("data", "").strip()
    turno   = form_data.get("turno", "").strip()
    setor   = form_data.get("setor", "").strip()
    linha   = form_data.get("linha", "").strip()
    modelo  = form_data.get("modelo", "").strip()
    hora_in = form_data.get("hora_inicio_prevista", "").strip()

    if not data:
        raise ValueError("Data é obrigatória.")
    if turno not in TURNOS_VALIDOS:
        raise ValueError(f"Turno inválido: {turno}")
    if not setor:
        raise ValueError("Setor é obrigatório.")
    if not linha:
        raise ValueError("Linha é obrigatória.")
    if not modelo:
        raise ValueError("Modelo é obrigatório.")
    if not hora_in:
        raise ValueError("Hora de início é obrigatória.")

    try:
        datetime.strptime(data, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Data inválida.")

    try:
        hora_inicio = datetime.strptime(hora_in, "%H:%M").time()
    except ValueError:
        raise ValueError("Hora de início inválida.")

    try:
        qtd = int(form_data.get("quantidade_planejada", 0))
    except (ValueError, TypeError):
        raise ValueError("Quantidade deve ser um número inteiro.")
    if qtd <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")

    try:
        taxa = int(form_data.get("taxa_horaria", 0) or 0)
    except (ValueError, TypeError):
        taxa = 0

    op_id_raw = form_data.get("op_id", "")
    op_id = int(op_id_raw) if op_id_raw and str(op_id_raw).strip() else None

    hora_fim = calcular_hora_fim(hora_inicio, qtd, taxa, turno, setor, linha)

    return {
        "data":                  data,
        "turno":                 turno,
        "setor":                 setor,
        "linha":                 linha,
        "op_id":                 op_id,
        "modelo":                modelo,
        "quantidade_planejada":  qtd,
        "taxa_horaria":          taxa,
        "hora_inicio_prevista":  hora_in,
        "hora_fim_prevista":     hora_fim.strftime("%H:%M") if hora_fim else None,
        "observacao":            form_data.get("observacao", "").strip() or None,
    }


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def criar(form_data: dict, username: str = "") -> dict:
    data = _validar_e_montar(form_data)
    data["criado_por"] = username
    new_id = repo.inserir(data)
    return {"id": new_id, "hora_fim_prevista": data["hora_fim_prevista"]}


def atualizar(planejamento_id: int, form_data: dict) -> dict:
    existente = repo.buscar_por_id(planejamento_id)
    if not existente:
        raise ValueError("Planejamento não encontrado.")

    parcial = dict(form_data)
    parcial.setdefault("data",   str(existente["data"]))
    parcial.setdefault("turno",  existente["turno"])
    parcial.setdefault("setor",  existente["setor"])
    parcial.setdefault("linha",  existente["linha"])

    data = _validar_e_montar(parcial)
    repo.atualizar(planejamento_id, data)
    return {"hora_fim_prevista": data["hora_fim_prevista"]}


def atualizar_status(planejamento_id: int, status: str) -> None:
    if status not in STATUS_VALIDOS:
        raise ValueError(f"Status inválido: {status}")
    repo.atualizar_status(planejamento_id, status)


def excluir(planejamento_id: int) -> None:
    if not planejamento_id or planejamento_id <= 0:
        raise ValueError("ID inválido.")
    repo.excluir(planejamento_id)


def listar(data: str, turno: str = "", setor: str = "", linha: str = "") -> list:
    return repo.listar(data, turno, setor, linha)


def ops_disponiveis(setor: str = "") -> list:
    return repo.ops_abertas(setor)


def plano_de_voo(data: str) -> dict:
    registros = repo.listar_plano_de_voo(data)
    agrupado: dict = {}
    for r in registros:
        agrupado.setdefault(r["linha"], []).append(dict(r))
    return agrupado


def opcoes_linha() -> dict:
    agrupado = lc_repo.listar_por_setor()
    return {setor: [r["linha"] for r in rows] for setor, rows in agrupado.items()}
