from app.extensions import get_db
from psycopg.rows import dict_row


def listar(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "") -> list:
    filtros = ["data BETWEEN %s AND %s"]
    params  = [data_inicial, data_final]

    if setor:
        filtros.append("setor = %s")
        params.append(setor)
    if linha:
        filtros.append("linha = %s")
        params.append(linha)
    if turno:
        filtros.append("turno = %s")
        params.append(turno)

    where = " AND ".join(filtros)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT
                    id, data, setor, linha, turno, semana, modelo, familia,
                    hora_inicio, hora_fim, intervalo,
                    producao_real, qtd_perda, defeitos,
                    codigo_parada, descricao_parada, observacao,
                    coletado_em
                FROM producao_coletada
                WHERE {where}
                ORDER BY data DESC, setor, linha, hora_inicio
            """, params)
            return cur.fetchall()


def totais(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "") -> dict:
    filtros = ["data BETWEEN %s AND %s"]
    params  = [data_inicial, data_final]

    if setor:
        filtros.append("setor = %s")
        params.append(setor)
    if linha:
        filtros.append("linha = %s")
        params.append(linha)
    if turno:
        filtros.append("turno = %s")
        params.append(turno)

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
