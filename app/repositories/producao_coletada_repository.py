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
        filtros.append("turno ILIKE %s")
        params.append(f"%{turno}%")

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
        filtros.append("turno ILIKE %s")
        params.append(f"%{turno}%")

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
            cur.execute("SELECT DISTINCT setor FROM producao_coletada WHERE setor IS NOT NULL ORDER BY setor")
            return [r[0] for r in cur.fetchall()]


def linhas_disponiveis(setor: str = "") -> list:
    with get_db() as conn:
        with conn.cursor() as cur:
            if setor:
                cur.execute(
                    "SELECT DISTINCT linha FROM producao_coletada WHERE setor = %s AND linha IS NOT NULL ORDER BY linha",
                    (setor,)
                )
            else:
                cur.execute("SELECT DISTINCT linha FROM producao_coletada WHERE linha IS NOT NULL ORDER BY linha")
            return [r[0] for r in cur.fetchall()]
