from app.extensions import get_db
from psycopg.rows import dict_row


def listar_locais(cliente: str = "") -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if cliente:
                cur.execute(
                    "SELECT * FROM local_entrega WHERE ativo = TRUE AND cliente ILIKE %s ORDER BY cliente, nome_local",
                    (f"%{cliente}%",)
                )
            else:
                cur.execute(
                    "SELECT * FROM local_entrega WHERE ativo = TRUE ORDER BY cliente, nome_local"
                )
            return cur.fetchall()


def buscar_local(local_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM local_entrega WHERE id = %s", (local_id,))
            return cur.fetchone()


def criar_local(cliente: str, nome_local: str, endereco: str,
                lat: float | None, lng: float | None) -> int:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO local_entrega (cliente, nome_local, endereco, lat, lng)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (cliente, nome_local, endereco or None, lat, lng))
            return cur.fetchone()["id"]


def atualizar_local(local_id: int, cliente: str, nome_local: str, endereco: str,
                    lat: float | None, lng: float | None) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE local_entrega
                SET cliente = %s, nome_local = %s, endereco = %s, lat = %s, lng = %s
                WHERE id = %s
            """, (cliente, nome_local, endereco or None, lat, lng, local_id))


def excluir_local(local_id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE local_entrega SET ativo = FALSE WHERE id = %s", (local_id,))
