from app.extensions import get_db
from psycopg.rows import dict_row


_SCHEMA_READY: bool = False


def _ensure_schema() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS linha_lider (
                    setor TEXT NOT NULL,
                    linha TEXT NOT NULL,
                    turno TEXT NOT NULL,
                    lider TEXT NOT NULL DEFAULT '',
                    hc    INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (setor, linha, turno)
                )
            """)
        conn.commit()

    _SCHEMA_READY = True


def listar() -> list:
    _ensure_schema()
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT setor, linha, turno, lider, hc
                FROM linha_lider
                ORDER BY setor, linha, turno
            """)
            return cur.fetchall()


def buscar(setor: str, linha: str, turno: str) -> dict | None:
    _ensure_schema()
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT setor, linha, turno, lider, hc
                FROM linha_lider
                WHERE setor = %s AND linha = %s AND turno = %s
            """, (setor, linha, turno))
            return cur.fetchone()


def salvar(setor: str, linha: str, turno: str, lider: str, hc: int) -> None:
    _ensure_schema()
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO linha_lider (setor, linha, turno, lider, hc)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (setor, linha, turno)
                DO UPDATE SET lider = EXCLUDED.lider, hc = EXCLUDED.hc
            """, (setor, linha, turno, lider, hc))
        conn.commit()


def excluir(setor: str, linha: str, turno: str) -> None:
    _ensure_schema()
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM linha_lider
                WHERE setor = %s AND linha = %s AND turno = %s
            """, (setor, linha, turno))
        conn.commit()
