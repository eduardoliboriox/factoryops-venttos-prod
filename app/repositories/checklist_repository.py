from app.database import get_db


def list_itens():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, numero, descricao FROM checklist_itens WHERE is_active = TRUE ORDER BY numero"
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def create_sessao(data: dict) -> int:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO checklist_sessoes (setor, linha, modelo, mes, responsavel, user_id, data_sessao)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    data["setor"],
                    data["linha"],
                    data.get("modelo") or None,
                    data.get("mes") or None,
                    data.get("responsavel") or None,
                    data["user_id"],
                    data.get("data_sessao") or "now()",
                ),
            )
            sessao_id = cur.fetchone()[0]
            conn.commit()
            return sessao_id


def create_respostas(sessao_id: int, respostas: list, user_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            for r in respostas:
                cur.execute(
                    """
                    INSERT INTO checklist_respostas (sessao_id, item_id, status, observacao, user_id)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        sessao_id,
                        r["item_id"],
                        r["status"],
                        r.get("observacao") or None,
                        user_id,
                    ),
                )
            conn.commit()


def create_plano_acao(data: dict):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO checklist_plano_acao
                    (sessao_id, item_id, problema, causa, acao, quando, responsavel, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data["sessao_id"],
                    data["item_id"],
                    data["problema"],
                    data.get("causa") or None,
                    data.get("acao") or None,
                    data.get("quando") or None,
                    data.get("responsavel") or None,
                    data.get("status", "Aberto"),
                ),
            )
            conn.commit()


def get_sessao_detail(sessao_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.id, s.setor, s.linha, s.modelo, s.mes, s.responsavel,
                       s.data_sessao, s.created_at, u.username
                FROM checklist_sessoes s
                LEFT JOIN users u ON u.id = s.user_id
                WHERE s.id = %s
                """,
                (sessao_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            sessao = dict(zip(cols, row))

            cur.execute(
                """
                SELECT r.item_id, i.numero, i.descricao, r.status, r.observacao,
                       r.created_at, u.username AS respondido_por
                FROM checklist_respostas r
                JOIN checklist_itens i ON i.id = r.item_id
                LEFT JOIN users u ON u.id = r.user_id
                WHERE r.sessao_id = %s
                ORDER BY i.numero
                """,
                (sessao_id,),
            )
            cols_r = [d[0] for d in cur.description]
            sessao["respostas"] = [dict(zip(cols_r, r)) for r in cur.fetchall()]

            cur.execute(
                """
                SELECT p.id, p.item_id, i.numero, p.problema, p.causa, p.acao,
                       p.quando, p.responsavel, p.status, p.created_at
                FROM checklist_plano_acao p
                JOIN checklist_itens i ON i.id = p.item_id
                WHERE p.sessao_id = %s
                ORDER BY i.numero
                """,
                (sessao_id,),
            )
            cols_p = [d[0] for d in cur.description]
            sessao["plano_acao"] = [dict(zip(cols_p, r)) for r in cur.fetchall()]

            return sessao


def list_sessoes(data_sessao=None, setor=None, linha=None, limit: int = 50) -> list:
    with get_db() as conn:
        with conn.cursor() as cur:
            conditions = []
            params = []

            if data_sessao:
                conditions.append("s.data_sessao = %s")
                params.append(data_sessao)
            if setor:
                conditions.append("s.setor = %s")
                params.append(setor)
            if linha:
                conditions.append("s.linha = %s")
                params.append(linha)

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            cur.execute(
                f"""
                SELECT s.id, s.setor, s.linha, s.modelo, s.data_sessao, s.created_at,
                       u.username,
                       (SELECT COUNT(*) FROM checklist_respostas r WHERE r.sessao_id = s.id) AS total_respostas,
                       (SELECT COUNT(*) FROM checklist_respostas r WHERE r.sessao_id = s.id AND r.status = 'nok') AS total_nok
                FROM checklist_sessoes s
                LEFT JOIN users u ON u.id = s.user_id
                {where}
                ORDER BY s.created_at DESC
                LIMIT %s
                """,
                params + [limit],
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
