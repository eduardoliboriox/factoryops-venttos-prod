from app.extensions import get_db
from psycopg.rows import dict_row


def listar() -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, turno, hora_inicio, hora_fim, ordem
                FROM turno_config
                ORDER BY ordem
            """)
            return cur.fetchall()


def inserir(turno: str, hora_inicio: str, hora_fim: str, ordem: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO turno_config (turno, hora_inicio, hora_fim, ordem)
                VALUES (%s, %s, %s, %s)
            """, (turno, hora_inicio, hora_fim, ordem))


def excluir(id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM turno_config WHERE id = %s", (id,))


def proximo_ordem(turno: str) -> int:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(ordem), 0) + 1 FROM turno_config WHERE turno = %s",
                (turno,)
            )
            return cur.fetchone()[0]
