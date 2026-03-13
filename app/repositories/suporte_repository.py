from app.extensions import get_db
from psycopg.rows import dict_row


def list_faq_items():
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, pergunta, resposta, categoria
                FROM faq_items
                WHERE is_active = TRUE
                ORDER BY categoria, ordem, id
            """)
            return cur.fetchall()


def create_ouvidoria_message(data: dict):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ouvidoria_messages (tipo, mensagem, nome_contato, user_id)
                VALUES (%s, %s, %s, %s)
            """, (
                data["tipo"],
                data["mensagem"],
                data.get("nome_contato"),
                data.get("user_id"),
            ))
            conn.commit()


def get_or_create_ticket(user_id: int):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT * FROM support_tickets
                WHERE user_id = %s AND status = 'open'
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            ticket = cur.fetchone()

        if ticket:
            return ticket

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO support_tickets (user_id, assunto, status)
                VALUES (%s, %s, 'open')
                RETURNING *
            """, (user_id, "Suporte geral"))
            conn.commit()
            return cur.fetchone()


def list_ticket_messages(ticket_id: int):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT sm.*, u.username, u.full_name
                FROM support_messages sm
                LEFT JOIN users u ON u.id = sm.user_id
                WHERE sm.ticket_id = %s
                ORDER BY sm.created_at ASC
            """, (ticket_id,))
            return cur.fetchall()


def create_ticket_message(data: dict):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO support_messages (ticket_id, user_id, is_support, mensagem)
                VALUES (%s, %s, %s, %s)
            """, (
                data["ticket_id"],
                data.get("user_id"),
                data.get("is_support", False),
                data["mensagem"],
            ))
            conn.commit()
