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


def list_all_tickets():
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT st.*, u.username, u.full_name,
                       (SELECT COUNT(*) FROM support_messages sm WHERE sm.ticket_id = st.id) AS total_messages,
                       (SELECT MAX(sm2.created_at) FROM support_messages sm2 WHERE sm2.ticket_id = st.id) AS last_message_at
                FROM support_tickets st
                LEFT JOIN users u ON u.id = st.user_id
                ORDER BY st.status ASC, COALESCE(
                    (SELECT MAX(sm3.created_at) FROM support_messages sm3 WHERE sm3.ticket_id = st.id),
                    st.created_at
                ) DESC
            """)
            return cur.fetchall()


def get_ticket_by_id(ticket_id: int):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT st.*, u.username, u.full_name
                FROM support_tickets st
                LEFT JOIN users u ON u.id = st.user_id
                WHERE st.id = %s
            """, (ticket_id,))
            return cur.fetchone()


def close_ticket(ticket_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE support_tickets SET status = 'closed' WHERE id = %s
            """, (ticket_id,))
            conn.commit()
