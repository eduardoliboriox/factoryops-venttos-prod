from app.extensions import get_db
from psycopg.rows import dict_row


def listar_por_filial_setor() -> dict:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, filial, setor, linha FROM linha_config ORDER BY filial, setor, linha"
            )
            rows = cur.fetchall()
    resultado = {}
    for r in rows:
        resultado.setdefault(r["filial"], {}).setdefault(r["setor"], []).append(r)
    return resultado


def listar_por_setor() -> dict:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, filial, setor, linha FROM linha_config ORDER BY filial, setor, linha"
            )
            rows = cur.fetchall()
    resultado = {}
    for r in rows:
        if r["filial"] == "VTT":
            resultado.setdefault("VTT", []).append(r)
        else:
            resultado.setdefault(r["setor"], []).append(r)
    return resultado


def listar_linhas_producao() -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT pc.linha, lc.filial AS filial_config, lc.setor AS setor_config, lc.id AS config_id
                FROM (
                    SELECT DISTINCT linha FROM producao_coletada
                    WHERE linha IS NOT NULL AND linha != ''
                ) pc
                LEFT JOIN linha_config lc ON lc.linha = pc.linha
                ORDER BY pc.linha
            """)
            return cur.fetchall()


def atribuir(filial: str, setor: str, linha: str) -> int:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO linha_config (filial, setor, linha)
                VALUES (%s, %s, %s)
                ON CONFLICT (linha) DO UPDATE SET filial = EXCLUDED.filial, setor = EXCLUDED.setor
                RETURNING id
            """, (filial, setor, linha))
            return cur.fetchone()["id"]


def remover(id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM linha_config WHERE id = %s", (id,))
