from __future__ import annotations
from datetime import datetime, time

from app.repositories import planejamento_repository as repo
from app.repositories import linha_config_repository as lc_repo

TURNOS_VALIDOS  = ["1º Turno", "2º Turno", "3º Turno"]
STATUS_VALIDOS  = {"PLANEJADO", "EM_EXECUCAO", "CONCLUIDO", "CANCELADO"}


# ─── helpers de tempo ─────────────────────────────────────────────────────────

def _to_minutes(t) -> int:
    if isinstance(t, str):
        parts = t.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    return t.hour * 60 + t.minute


def _from_minutes(m: int) -> time:
    m = m % (24 * 60)
    return time(m // 60, m % 60)


def _intervalo_minutos(inicio: time, fim: time) -> int:
    s = _to_minutes(inicio)
    e = _to_minutes(fim)
    if e <= s:
        e += 24 * 60
    return e - s


def _overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    return max(0, min(a_end, b_end) - max(a_start, b_start))


def _hhmm_to_min(valor) -> int:
    if isinstance(valor, time):
        return _to_minutes(valor)
    if isinstance(valor, str) and ":" in valor:
        h, m = map(int, valor.split(":"))
        return h * 60 + m
    return 0


# ─── setup sugerido por setor/linha ───────────────────────────────────────────

def setup_sugerido(setor: str, linha: str = "") -> int:
    s = (setor or "").upper()
    l = (linha or "").upper()
    if s == "PTH" and l.startswith("ROU"):
        return 20
    if s in ("IM", "PA"):
        return 30
    if s in ("SMD", "SMT"):
        return 60
    return 0


# ─── cálculo de hora_fim ──────────────────────────────────────────────────────

def calcular_hora_fim(
    hora_inicio: time,
    quantidade_planejada: int,
    taxa_horaria: int,
    turno: str,
    setor: str,
    linha: str,
    setup_min: int = 0,
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
    setup_restante    = setup_min
    cursor_min        = _to_minutes(hora_inicio)

    prev_iv_end = None
    for iv in intervalos:
        iv_start = _to_minutes(iv["hora_inicio"])
        iv_end   = _to_minutes(iv["hora_fim"])
        if iv_end <= iv_start:
            iv_end += 24 * 60
        if prev_iv_end is not None and iv_start < prev_iv_end:
            iv_start += 24 * 60
            iv_end   += 24 * 60
        prev_iv_end = iv_end

        janela_start = max(cursor_min, iv_start)
        if janela_start >= iv_end:
            continue

        brutos = iv_end - janela_start

        paradas_na_janela = sum(
            _overlap(janela_start, iv_end, p_s, p_e)
            for p_s, p_e in paradas_min
        )
        disponivel = max(0, brutos - paradas_na_janela)

        setup_aqui     = min(setup_restante, disponivel)
        setup_restante -= setup_aqui
        uteis          = disponivel - setup_aqui

        if uteis <= 0:
            cursor_min = iv_end
            continue

        if uteis >= minutos_restantes:
            fim_min = janela_start + setup_aqui + minutos_restantes + paradas_na_janela * (minutos_restantes / uteis)
            return _from_minutes(int(fim_min))
        else:
            minutos_restantes -= uteis
            cursor_min = iv_end

    return None


# ─── plano hora a hora ────────────────────────────────────────────────────────

def gerar_plano_hora_a_hora(
    planos: list,
    turno_intervalos: list,
    paradas: list,
    data_str: str,
) -> list:
    """
    Simula hora a hora todos os planejamentos de uma linha num dia.
    Retorna lista de slots com detalhes de setup, paradas e produção.
    """
    dow = datetime.strptime(data_str, "%Y-%m-%d").weekday()
    dia_codigo = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"][dow]

    paradas_ativas = [
        p for p in paradas
        if not p.get("frequencia_dias") or dia_codigo in p["frequencia_dias"].split(",")
    ]

    janelas = []
    for iv in turno_intervalos:
        s = _to_minutes(iv["hora_inicio"])
        e = _to_minutes(iv["hora_fim"])
        if e <= s:
            e += 24 * 60
        if janelas and s < janelas[-1][1]:
            s += 24 * 60
            e += 24 * 60
        janelas.append((s, e))

    if not janelas or not planos:
        return []

    turno_cruza_meia_noite = janelas[-1][1] > 24 * 60
    turno_inicio_min       = janelas[0][0]

    paradas_intervals = []
    for p in paradas_ativas:
        if p["hora_inicio"]:
            s    = _to_minutes(p["hora_inicio"])
            e    = s + p["duracao_min"]
            tipo = p.get("tipo", "PARADA")
            paradas_intervals.append((s, e, tipo))
            if turno_cruza_meia_noite and s < turno_inicio_min:
                paradas_intervals.append((s + 24 * 60, e + 24 * 60, tipo))

    slots         = []
    total_acumulado = 0
    cursor_min    = None

    for plano in planos:
        hi_min = _hhmm_to_min(plano.get("hora_inicio_prevista"))

        if cursor_min is None:
            cursor_min = hi_min

        remaining      = plano["quantidade_planejada"]
        taxa           = plano.get("taxa_horaria") or 0
        setup_restante = plano.get("setup_min") or 0
        plano_concluido = False

        for janela_start, janela_end in janelas:
            if plano_concluido:
                break
            if cursor_min >= janela_end:
                continue

            slot_cursor = max(cursor_min, janela_start)

            while slot_cursor < janela_end and not plano_concluido:
                slot_inicio   = slot_cursor
                slot_fim      = min(slot_cursor + 60, janela_end)
                slot_duracao  = slot_fim - slot_inicio

                paradas_slot     = []
                paradas_min_slot = 0
                for p_start, p_end, p_tipo in paradas_intervals:
                    ov = _overlap(slot_inicio, slot_fim, p_start, p_end)
                    if ov > 0:
                        paradas_slot.append({"tipo": p_tipo, "duracao": ov})
                        paradas_min_slot += ov

                disponivel     = max(0, slot_duracao - paradas_min_slot)
                setup_no_slot  = min(setup_restante, disponivel)
                setup_restante -= setup_no_slot
                producao_min   = max(0, disponivel - setup_no_slot)

                if taxa > 0:
                    pecas = min(remaining, round((producao_min / 60.0) * taxa))
                else:
                    pecas = 0

                remaining       -= pecas
                total_acumulado += pecas
                concluiu         = remaining <= 0

                if concluiu and pecas > 0 and taxa > 0:
                    min_real   = (pecas / taxa) * 60
                    fim_real   = slot_inicio + paradas_min_slot + setup_no_slot + min_real
                    hora_fim_s = _from_minutes(int(fim_real)).strftime("%H:%M")
                    cursor_min = int(fim_real)
                else:
                    hora_fim_s = _from_minutes(slot_fim).strftime("%H:%M")
                    cursor_min = slot_fim

                slots.append({
                    "hora_inicio":     _from_minutes(slot_inicio).strftime("%H:%M"),
                    "hora_fim":        hora_fim_s,
                    "modelo":          plano.get("modelo", ""),
                    "op_numero":       plano.get("numero_op") or "",
                    "setup_min":       setup_no_slot,
                    "paradas":         paradas_slot,
                    "paradas_min":     paradas_min_slot,
                    "producao_min":    producao_min,
                    "pecas":           pecas,
                    "total_acumulado": total_acumulado,
                    "concluiu":        concluiu,
                    "meta_hora":       taxa,
                })

                if concluiu:
                    plano_concluido = True
                    break

                slot_cursor = slot_fim

        if not plano_concluido and janelas:
            cursor_min = janelas[-1][1]

    return slots


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

    try:
        setup = int(form_data.get("setup_min", 0) or 0)
    except (ValueError, TypeError):
        setup = 0
    if setup < 0:
        setup = 0

    op_id_raw = form_data.get("op_id", "")
    op_id = int(op_id_raw) if op_id_raw and str(op_id_raw).strip() else None

    hora_fim = calcular_hora_fim(hora_inicio, qtd, taxa, turno, setor, linha, setup)

    return {
        "data":                  data,
        "turno":                 turno,
        "setor":                 setor,
        "linha":                 linha,
        "op_id":                 op_id,
        "modelo":                modelo,
        "quantidade_planejada":  qtd,
        "taxa_horaria":          taxa,
        "setup_min":             setup,
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


def planos_agrupados_por_linha(data: str) -> list:
    registros = repo.listar(data)
    grupos: dict = {}
    for p in registros:
        key = (p["turno"], p["setor"], p["linha"])
        if key not in grupos:
            grupos[key] = {
                "turno":       p["turno"],
                "setor":       p["setor"],
                "linha":       p["linha"],
                "data":        str(p["data"]),
                "modelos":     [],
                "meta_total":  0,
                "hora_inicio": str(p.get("hora_inicio_prevista") or ""),
            }
        grupos[key]["modelos"].append(p["modelo"])
        grupos[key]["meta_total"] += int(p.get("quantidade_planejada") or 0)
    return list(grupos.values())


def resumo_producao(data_str: str, turno: str = "", setor: str = "") -> list:
    linhas_config = opcoes_linha()
    registros = repo.listar(data_str, turno)

    planos_por_key: dict = {}
    for p in registros:
        key = (p["setor"], p["linha"])
        planos_por_key.setdefault(key, []).append(dict(p))

    resultado = []
    for s in sorted(linhas_config):
        if setor and s != setor:
            continue
        grupo = {"setor": s, "linhas": []}
        for linha in sorted(linhas_config[s]):
            planos_linha = planos_por_key.get((s, linha), [])
            grupo["linhas"].append({
                "linha":     linha,
                "planos":    planos_linha,
                "sem_plano": not planos_linha,
            })
        resultado.append(grupo)

    return resultado


def dados_impressao_plano_voo(data_str: str, turno: str, setor: str, linha: str) -> dict:
    planos     = repo.listar_plano_de_voo(data_str, turno=turno, setor=setor, linha=linha)
    intervalos = repo.turno_intervalos(turno)
    paradas    = repo.paradas_da_linha(setor, linha)

    slots = gerar_plano_hora_a_hora(
        [dict(p) for p in planos],
        [dict(i) for i in intervalos],
        [dict(p) for p in paradas],
        data_str,
    ) if planos else []

    primeiro     = dict(planos[0]) if planos else {}
    modelo       = primeiro.get("modelo", "")
    familia      = repo.familia_por_modelo(modelo) if modelo else None
    cliente      = familia.strip().split()[0] if familia else "—"
    meta_diaria  = sum(p.get("quantidade_planejada", 0) for p in planos)
    responsavel  = primeiro.get("criado_por", "") or "—"

    return {
        "slots":  slots,
        "data":   data_str,
        "info": {
            "cliente":     cliente,
            "setor":       setor or primeiro.get("setor", ""),
            "linha":       linha or primeiro.get("linha", ""),
            "produto":     modelo,
            "meta_diaria": meta_diaria,
            "turno":       turno,
            "responsavel": responsavel,
        },
    }
