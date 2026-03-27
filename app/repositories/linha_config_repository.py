from app.extensions import get_db
from psycopg.rows import dict_row


def listar_por_setor() -> dict:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT id, setor, linha FROM linha_config ORDER BY setor, linha")
            rows = cur.fetchall()
    resultado = {}
    for r in rows:
        resultado.setdefault(r["setor"], []).append(r)
    return resultado


def listar_linhas_producao() -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT pc.linha, lc.setor AS setor_config, lc.id AS config_id
                FROM (
                    SELECT DISTINCT linha FROM producao_coletada
                    WHERE linha IS NOT NULL AND linha != ''
                ) pc
                LEFT JOIN linha_config lc ON lc.linha = pc.linha
                ORDER BY pc.linha
            """)
            return cur.fetchall()


def atribuir(setor: str, linha: str) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO linha_config (setor, linha)
                VALUES (%s, %s)
                ON CONFLICT (linha) DO UPDATE SET setor = EXCLUDED.setor
            """, (setor, linha))


def remover(id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM linha_config WHERE id = %s", (id,))
