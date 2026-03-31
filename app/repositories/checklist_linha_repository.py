import datetime
from psycopg.rows import dict_row
from app.extensions import get_db


def create_registro(data: dict, user_id: int) -> dict:
    ano = data.get("ano") or datetime.date.today().year
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT COALESCE(MAX(sequencia), 0) + 1 AS next_seq FROM checklist_linha_registros WHERE ano=%s",
                (ano,),
            )
            sequencia = cur.fetchone()["next_seq"]
            doc_id = f"CL-{sequencia}-{ano}"
            cur.execute(
                """
                INSERT INTO checklist_linha_registros
                (doc_id, ano, sequencia, mes, setor, linha, turno, modelo, created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    doc_id,
                    ano,
                    sequencia,
                    data.get("mes"),
                    data.get("setor"),
                    data.get("linha"),
                    data.get("turno") or None,
                    data.get("modelo") or None,
                    user_id,
                ),
            )
            registro = cur.fetchone()
        conn.commit()
    return registro


def update_registro(registro_id: int, data: dict) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                UPDATE checklist_linha_registros
                SET mes=%s, setor=%s, linha=%s, turno=%s, modelo=%s
                WHERE id=%s
                RETURNING *
                """,
                (
                    data.get("mes"),
                    data.get("setor"),
                    data.get("linha"),
                    data.get("turno") or None,
                    data.get("modelo") or None,
                    registro_id,
                ),
            )
            registro = cur.fetchone()
        conn.commit()
    return registro


def upsert_entradas(registro_id: int, entradas: list):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM checklist_linha_entradas WHERE registro_id=%s",
                (registro_id,),
            )
            for e in entradas:
                cur.execute(
                    """
                    INSERT INTO checklist_linha_entradas (registro_id, item_num, dia, status)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (registro_id, int(e["item_num"]), int(e["dia"]), e["status"]),
                )
        conn.commit()


def upsert_assinaturas(registro_id: int, assinaturas: list):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM checklist_linha_assinaturas WHERE registro_id=%s",
                (registro_id,),
            )
            for a in assinaturas:
                cur.execute(
                    """
                    INSERT INTO checklist_linha_assinaturas (registro_id, dia, username, timestamp)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (registro_id, int(a["dia"]), a["username"], a.get("timestamp")),
                )
        conn.commit()


def upsert_plano_acao(registro_id: int, itens: list, user_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM checklist_linha_plano_acao WHERE registro_id=%s",
                (registro_id,),
            )
            for item in itens:
                if not (item.get("problema") or "").strip():
                    continue
                cur.execute(
                    """
                    INSERT INTO checklist_linha_plano_acao
                    (registro_id, dia, item_num, problema, causa, acao, quando, responsavel, created_by)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        registro_id,
                        item.get("dia") or None,
                        item.get("item_num") or None,
                        item["problema"].strip(),
                        item.get("causa") or None,
                        item.get("acao") or None,
                        item.get("quando") or None,
                        item.get("responsavel") or None,
                        user_id,
                    ),
                )
        conn.commit()


def get_registro_by_id(registro_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT r.*, u.username
                FROM checklist_linha_registros r
                LEFT JOIN users u ON u.id = r.created_by
                WHERE r.id=%s
                """,
                (registro_id,),
            )
            registro = cur.fetchone()
            if not registro:
                return None
            cur.execute(
                """
                SELECT item_num, dia, status
                FROM checklist_linha_entradas
                WHERE registro_id=%s
                ORDER BY item_num, dia
                """,
                (registro_id,),
            )
            entradas = cur.fetchall()
            cur.execute(
                """
                SELECT dia, username, timestamp
                FROM checklist_linha_assinaturas
                WHERE registro_id=%s
                ORDER BY dia
                """,
                (registro_id,),
            )
            assinaturas = cur.fetchall()
    return {**registro, "entradas": list(entradas), "assinaturas": list(assinaturas)}


def get_plano_by_registro_id(registro_id: int) -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT dia, item_num, problema, causa, acao, quando, responsavel
                FROM checklist_linha_plano_acao
                WHERE registro_id=%s
                ORDER BY id
                """,
                (registro_id,),
            )
            return cur.fetchall()


def list_registros(mes=None, ano=None, setor=None, linha=None, limit=100) -> list:
    filters = []
    params = []
    if mes:
        filters.append("r.mes=%s")
        params.append(mes)
    if ano:
        filters.append("r.ano=%s")
        params.append(ano)
    if setor:
        filters.append("r.setor=%s")
        params.append(setor)
    if linha:
        filters.append("r.linha=%s")
        params.append(linha)
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    params.append(limit)
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT r.id, r.doc_id, r.mes, r.ano, r.setor, r.linha, r.turno,
                       r.modelo, r.created_at, u.username
                FROM checklist_linha_registros r
                LEFT JOIN users u ON u.id = r.created_by
                {where}
                ORDER BY r.created_at DESC
                LIMIT %s
                """,
                params,
            )
            return cur.fetchall()
