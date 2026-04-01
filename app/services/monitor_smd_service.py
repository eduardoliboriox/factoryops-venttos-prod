from datetime import date, datetime, time
from app.repositories import linha_config_repository as lc_repo
from app.repositories import turno_config_repository as tc_repo
from app.extensions import get_db
from psycopg.rows import dict_row

SETOR = "SMD"


def _to_time(val) -> time:
    if isinstance(val, time):
        return val
    if hasattr(val, 'hour'):
        return time(val.hour, val.minute)
    parts = str(val).split(':')
    return time(int(parts[0]), int(parts[1]))


def _turno_atual(turnos: list) -> dict | None:
    agora = datetime.now().time()
    for t in turnos:
        ini = _to_time(t["hora_inicio"])
        fim = _to_time(t["hora_fim"])
        if ini <= fim:
            if ini <= agora < fim:
                return t
        else:
            if agora >= ini or agora < fim:
                return t
    return None


def _slots_turno(turno: dict) -> list[time]:
    ini: time = _to_time(turno["hora_inicio"])
    fim: time = _to_time(turno["hora_fim"])
    slots = []
    h = ini.hour
    for _ in range(24):
        slots.append(time(h % 24, 0))
        h += 1
        if ini <= fim:
            if (h % 24) >= fim.hour:
                break
        else:
            if h >= 24 and (h % 24) >= fim.hour:
                break
    return slots


def get_status_atual() -> dict:
    hoje = date.today()
    agora = datetime.now().time()
    dia = hoje.day
    mes = hoje.month
    ano = hoje.year

    linhas_por_setor = lc_repo.listar_por_setor()
    linhas = [r["linha"] for r in linhas_por_setor.get(SETOR, [])]
    turnos = tc_repo.listar()
    turno = _turno_atual(turnos)
    slots = _slots_turno(turno) if turno else []

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT r.linha,
                       EXTRACT(HOUR FROM h.horario_inicio)::int AS hora,
                       h.status
                FROM limpeza_stencil_registros r
                JOIN limpeza_stencil_horarios h ON h.registro_id = r.id
                WHERE r.data = %s AND r.setor = %s
            """, (hoje, SETOR))
            ls_rows = cur.fetchall()

            cur.execute("""
                SELECT DISTINCT linha
                FROM medicao_pasta_registros
                WHERE data = %s AND setor = %s
            """, (hoje, SETOR))
            mp_rows = cur.fetchall()

            cur.execute("""
                SELECT DISTINCT r.linha
                FROM checklist_linha_registros r
                JOIN checklist_linha_entradas e ON e.registro_id = r.id
                WHERE r.setor = %s
                  AND r.ano = %s
                  AND EXTRACT(MONTH FROM r.created_at) = %s
                  AND e.dia = %s
                  AND e.status IS NOT NULL
            """, (SETOR, ano, mes, dia))
            cl_rows = cur.fetchall()

    ls_map: dict[str, dict[int, bool]] = {}
    for row in ls_rows:
        l = row["linha"]
        h = row["hora"]
        done = bool(row["status"])
        ls_map.setdefault(l, {})[h] = ls_map.get(l, {}).get(h, False) or done

    mp_set = {row["linha"] for row in mp_rows}
    cl_set = {row["linha"] for row in cl_rows}

    result_linhas = []
    for linha in linhas:
        horas_status = []
        for slot in slots:
            passou = agora >= slot
            ls_done = ls_map.get(linha, {}).get(slot.hour, False)
            if not passou:
                ls = "blue"
            elif ls_done:
                ls = "green"
            else:
                ls = "red"
            horas_status.append({"hora": slot.strftime("%H:%M"), "passou": passou, "ls": ls})

        if not turno:
            mp = "blue"
            cl = "blue"
        else:
            mp = "green" if linha in mp_set else "red"
            cl = "green" if linha in cl_set else "red"

        result_linhas.append({"linha": linha, "cl": cl, "mp": mp, "horas": horas_status})

    return {
        "linhas": result_linhas,
        "turno_nome": turno["turno"] if turno else "Fora de turno",
        "slots": [s.strftime("%H:%M") for s in slots],
        "hoje": hoje.strftime("%d/%m/%Y"),
        "atualizado_em": datetime.now().strftime("%H:%M:%S"),
        "tem_turno": turno is not None,
    }
