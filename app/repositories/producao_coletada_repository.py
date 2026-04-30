from app.extensions import get_db
from psycopg.rows import dict_row


def _where_turno_noturno(
    data_inicial: str, data_final: str, turno: str,
    hora_inicio_turno, hora_fim_turno
) -> tuple[str, list]:
    filtro = (
        "turno = %s AND ("
        "(data BETWEEN %s AND %s AND NULLIF(hora_inicio, '')::time >= %s)"
        " OR "
        "(data BETWEEN %s::date + INTERVAL '1 day' AND %s::date + INTERVAL '1 day'"
        " AND NULLIF(hora_inicio, '')::time <= %s)"
        ")"
    )
    params = [turno, data_inicial, data_final, hora_inicio_turno,
              data_inicial, data_final, hora_fim_turno]
    return filtro, params


def listar(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "",
           hora_inicio_turno=None, hora_fim_turno=None) -> list:
    if hora_inicio_turno is not None and hora_fim_turno is not None:
        where_base, params = _where_turno_noturno(
            data_inicial, data_final, turno, hora_inicio_turno, hora_fim_turno
        )
        filtros = [where_base, "origem != 'mes'"]
    else:
        filtros = ["origem != 'mes'", "data BETWEEN %s AND %s"]
        params  = [data_inicial, data_final]
        if turno:
            filtros.append("turno = %s")
            params.append(turno)

    if setor:
        filtros.append("setor = %s")
        params.append(setor)
    if linha:
        filtros.append("linha = %s")
        params.append(linha)

    where = " AND ".join(filtros)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT
                    id, data, setor, linha, turno, semana, modelo, familia,
                    hora_inicio, hora_fim, intervalo,
                    producao_real, qtd_perda, defeitos,
                    codigo_parada, descricao_parada, observacao,
                    coletado_em, origem
                FROM producao_coletada
                WHERE {where}
                ORDER BY data DESC, setor, linha, hora_inicio
            """, params)
            return cur.fetchall()


def totais(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "",
           hora_inicio_turno=None, hora_fim_turno=None) -> dict:
    if hora_inicio_turno is not None and hora_fim_turno is not None:
        where_base, params = _where_turno_noturno(
            data_inicial, data_final, turno, hora_inicio_turno, hora_fim_turno
        )
        filtros = [where_base, "origem != 'mes'"]
    else:
        filtros = ["origem != 'mes'", "data BETWEEN %s AND %s"]
        params  = [data_inicial, data_final]
        if turno:
            filtros.append("turno = %s")
            params.append(turno)

    if setor:
        filtros.append("setor = %s")
        params.append(setor)
    if linha:
        filtros.append("linha = %s")
        params.append(linha)

    where = " AND ".join(filtros)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT
                    COUNT(*)                    AS total_registros,
                    COALESCE(SUM(producao_real), 0) AS producao_total,
                    COALESCE(SUM(qtd_perda),     0) AS perda_total,
                    COALESCE(SUM(defeitos),       0) AS defeitos_total
                FROM producao_coletada
                WHERE {where}
            """, params)
            return cur.fetchone() or {}


def setores_disponiveis() -> list:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT setor FROM linha_config ORDER BY setor")
            return [r["setor"] for r in cur.fetchall()]


def linhas_disponiveis(setor: str = "") -> list:
    with get_db() as conn:
        with conn.cursor() as cur:
            if setor:
                cur.execute(
                    "SELECT linha FROM linha_config WHERE setor = %s ORDER BY linha",
                    (setor,)
                )
            else:
                cur.execute("SELECT linha FROM linha_config ORDER BY linha")
            return [r["linha"] for r in cur.fetchall()]


def inserir_manual(data: dict) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT nextval('producao_coletada_manual_seq')")
            manual_id = cur.fetchone()["nextval"]
            cur.execute("""
                INSERT INTO producao_coletada (
                    id, data, setor, linha, turno, modelo,
                    producao_real, qtd_perda, defeitos, observacao,
                    coletado_em, origem
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), 'manual')
            """, (
                manual_id,
                data["data"],
                data["setor"],
                data["linha"],
                data["turno"],
                data["modelo"],
                data["producao_real"],
                data.get("qtd_perda", 0),
                data.get("defeitos", 0),
                data.get("observacao") or None,
            ))


def buscar_manual_por_id(registro_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, data, turno, modelo, linha FROM producao_coletada WHERE id = %s AND origem = 'manual'",
                (registro_id,)
            )
            return cur.fetchone()


def excluir_manual(registro_id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM producao_coletada WHERE id = %s AND origem = 'manual'",
                (registro_id,)
            )


def listar_mes(data_inicial: str, data_final: str, setor: str = "", linha: str = "",
               turno: str = "") -> list:
    filtros = ["pc.origem = 'mes'", "pc.data BETWEEN %s AND %s"]
    params  = [data_inicial, data_final]
    if turno:
        filtros.append("pc.turno = %s")
        params.append(turno)
    if setor:
        filtros.append("(pc.setor = %s OR lc.setor = %s)")
        params.extend([setor, setor])
    if linha:
        filtros.append("pc.linha = %s")
        params.append(linha)

    where = " AND ".join(filtros)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT
                    pc.id, pc.data,
                    COALESCE(NULLIF(pc.setor, ''), lc.setor, '') AS setor,
                    pc.linha, pc.turno, pc.modelo,
                    pc.meta, pc.producao_real, pc.qtd_perda, pc.defeitos,
                    pc.observacao, pc.coletado_em
                FROM producao_coletada pc
                LEFT JOIN linha_config lc ON lc.linha = pc.linha
                WHERE {where}
                ORDER BY pc.data DESC, setor, pc.linha, pc.turno
            """, params)
            return cur.fetchall()


def totais_mes(data_inicial: str, data_final: str, setor: str = "", linha: str = "",
               turno: str = "") -> dict:
    filtros = ["origem = 'mes'", "data BETWEEN %s AND %s"]
    params  = [data_inicial, data_final]
    if turno:
        filtros.append("turno = %s")
        params.append(turno)
    if setor:
        filtros.append("setor = %s")
        params.append(setor)
    if linha:
        filtros.append("linha = %s")
        params.append(linha)

    where = " AND ".join(filtros)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT
                    COUNT(*)                        AS total_registros,
                    COALESCE(SUM(producao_real), 0) AS producao_total,
                    COALESCE(SUM(meta), 0)          AS meta_total,
                    COALESCE(SUM(qtd_perda), 0)     AS perda_total,
                    COALESCE(SUM(defeitos), 0)       AS defeitos_total,
                    CASE
                        WHEN COALESCE(SUM(meta), 0) > 0
                        THEN ROUND((SUM(producao_real)::numeric / SUM(meta)) * 100, 1)
                        ELSE NULL
                    END AS eficiencia_pct
                FROM producao_coletada
                WHERE {where}
            """, params)
            return cur.fetchone() or {}


def importar_registros_mes(registros: list) -> dict:
    if not registros:
        return {"salvos": 0, "erros": 0}

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                for r in registros:
                    cur.execute("""
                        INSERT INTO producao_coletada (
                            id, data, setor, linha, turno, semana, modelo, familia,
                            hora_inicio, hora_fim, intervalo,
                            producao_real, qtd_perda, defeitos, meta,
                            parada_seg, codigo_parada, descricao_parada,
                            observacao, coletado_em, origem
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, NOW(), 'mes'
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            producao_real    = EXCLUDED.producao_real,
                            qtd_perda        = EXCLUDED.qtd_perda,
                            defeitos         = EXCLUDED.defeitos,
                            meta             = EXCLUDED.meta,
                            observacao       = EXCLUDED.observacao,
                            coletado_em      = NOW()
                    """, (
                        r.get("id"),
                        r.get("data"),
                        r.get("setor", ""),
                        r.get("linha", ""),
                        r.get("turno", ""),
                        r.get("semana"),
                        r.get("modelo", ""),
                        r.get("familia"),
                        r.get("hora_inicio", ""),
                        r.get("hora_fim", ""),
                        r.get("intervalo", ""),
                        r.get("producao_real", 0),
                        r.get("qtd_perda", 0),
                        r.get("defeitos", 0),
                        r.get("meta"),
                        r.get("parada_seg"),
                        r.get("codigo_parada"),
                        r.get("descricao_parada"),
                        r.get("observacao"),
                    ))
        return {"salvos": len(registros), "erros": 0}
    except Exception:
        return {"salvos": 0, "erros": len(registros)}


def importar_registros(registros: list) -> dict:
    if not registros:
        return {"salvos": 0, "erros": 0}

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                for r in registros:
                    cur.execute("""
                        INSERT INTO producao_coletada (
                            id, data, setor, linha, turno, semana, modelo, familia,
                            hora_inicio, hora_fim, intervalo, producao_real, qtd_perda,
                            defeitos, parada_seg, codigo_parada, descricao_parada,
                            observacao, coletado_em
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, NOW()
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            producao_real    = EXCLUDED.producao_real,
                            qtd_perda        = EXCLUDED.qtd_perda,
                            defeitos         = EXCLUDED.defeitos,
                            descricao_parada = EXCLUDED.descricao_parada,
                            observacao       = EXCLUDED.observacao,
                            coletado_em      = NOW()
                    """, (
                        r.get("id"),
                        r.get("data"),
                        r.get("setor", ""),
                        r.get("linha", ""),
                        r.get("turno", ""),
                        r.get("semana"),
                        r.get("modelo", ""),
                        r.get("familia", ""),
                        r.get("hora_inicio", ""),
                        r.get("hora_fim", ""),
                        r.get("intervalo", ""),
                        r.get("producao_real", 0),
                        r.get("qtd_perda", 0),
                        r.get("defeitos", 0),
                        r.get("parada_seg"),
                        r.get("codigo_parada"),
                        r.get("descricao_parada"),
                        r.get("observacao"),
                    ))
        return {"salvos": len(registros), "erros": 0}
    except Exception:
        return {"salvos": 0, "erros": len(registros)}
