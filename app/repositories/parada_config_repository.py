from app.extensions import get_db
from psycopg.rows import dict_row


def listar() -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, setor, linha, tipo, nome, hora_inicio, duracao_min
                FROM parada_config
                ORDER BY setor, linha, hora_inicio NULLS LAST, nome
            """)
            return cur.fetchall()


def inserir(data: dict) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO parada_config (setor, linha, tipo, nome, hora_inicio, duracao_min)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                data.get("setor") or None,
                data.get("linha") or None,
                data["tipo"],
                data["nome"],
                data.get("hora_inicio") or None,
                data["duracao_min"],
            ))


def excluir(parada_id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM parada_config WHERE id = %s", (parada_id,))
