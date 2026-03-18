import datetime
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from app.extensions import get_db


def create_registro(data: dict, user_id: int) -> dict:
    turno = int(data["turno"]) if data.get("turno") else None
    ano   = datetime.date.today().year
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT COALESCE(MAX(sequencia), 0) + 1 FROM medicao_pasta_registros WHERE ano=%s",
                (ano,),
            )
            sequencia = cur.fetchone()["coalesce"]
            doc_id    = f"{sequencia}-{ano}"

            cur.execute(
                """
                INSERT INTO medicao_pasta_registros
                (data, cliente, espessura_stencil, turno, modelo, tolerancia,
                 lado, setor, linha, posi_mec, horas, created_by, ano, sequencia, doc_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    data["data"],
                    data.get("cliente"),
                    data.get("espessura_stencil"),
                    turno,
                    data.get("modelo"),
                    data.get("tolerancia"),
                    data.get("lado"),
                    data.get("setor"),
                    data["linha"],
                    Jsonb(data["posi_mec"]) if data.get("posi_mec") is not None else None,
                    Jsonb(data["horas"]) if data.get("horas") is not None else None,
                    user_id,
                    ano,
                    sequencia,
                    doc_id,
                ),
            )
            registro = cur.fetchone()
        conn.commit()
    return registro


def update_registro(registro_id: int, data: dict) -> dict | None:
    turno = int(data["turno"]) if data.get("turno") else None
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                UPDATE medicao_pasta_registros
                SET data=%s, cliente=%s, espessura_stencil=%s, turno=%s, modelo=%s,
                    tolerancia=%s, lado=%s, setor=%s, linha=%s, posi_mec=%s, horas=%s
                WHERE id=%s
                RETURNING *
                """,
                (
                    data["data"],
                    data.get("cliente"),
                    data.get("espessura_stencil"),
                    turno,
                    data.get("modelo"),
                    data.get("tolerancia"),
                    data.get("lado"),
                    data.get("setor"),
                    data["linha"],
                    Jsonb(data["posi_mec"]) if data.get("posi_mec") is not None else None,
                    Jsonb(data["horas"]) if data.get("horas") is not None else None,
                    registro_id,
                ),
            )
            registro = cur.fetchone()
        conn.commit()
    return registro


def upsert_medicoes(registro_id: int, medicoes: list):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM medicao_pasta_medicoes WHERE registro_id=%s",
                (registro_id,),
            )
            for m in medicoes:
                cur.execute(
                    """
                    INSERT INTO medicao_pasta_medicoes
                    (registro_id, componente, lado, tipo_medida, horarios)
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    (
                        registro_id,
                        int(m["componente"]),
                        m["lado"],
                        m["tipo_medida"],
                        Jsonb(m.get("horarios") or []),
                    ),
                )
        conn.commit()


def upsert_assinaturas(registro_id: int, assinaturas: list):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM medicao_pasta_assinaturas WHERE registro_id=%s",
                (registro_id,),
            )
            for a in assinaturas:
                cur.execute(
                    """
                    INSERT INTO medicao_pasta_assinaturas
                    (registro_id, campo, username, timestamp)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (
                        registro_id,
                        a["campo"],
                        a["username"],
                        a.get("timestamp"),
                    ),
                )
        conn.commit()


def get_registro_by_id(registro_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT r.*, u.username
                FROM medicao_pasta_registros r
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
                SELECT componente, lado, tipo_medida, horarios
                FROM medicao_pasta_medicoes
                WHERE registro_id=%s
                ORDER BY componente, lado, tipo_medida
                """,
                (registro_id,),
            )
            medicoes = cur.fetchall()

            cur.execute(
                """
                SELECT campo, username, timestamp
                FROM medicao_pasta_assinaturas
                WHERE registro_id=%s
                """,
                (registro_id,),
            )
            assinaturas = cur.fetchall()

    return {**registro, "medicoes": list(medicoes), "assinaturas": list(assinaturas)}


def list_registros(data=None, setor=None, linha=None, limit=100) -> list:
    filters = []
    params = []
    if data:
        filters.append("r.data=%s")
        params.append(data)
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
                SELECT r.id, r.doc_id, r.data, r.setor, r.linha, r.modelo, r.turno,
                       r.created_at, u.username
                FROM medicao_pasta_registros r
                LEFT JOIN users u ON u.id = r.created_by
                {where}
                ORDER BY r.created_at DESC
                LIMIT %s
                """,
                params,
            )
            return cur.fetchall()


def create_plano_acao_itens(itens: list, user_id: int, registro_id: int | None = None):
    with get_db() as conn:
        with conn.cursor() as cur:
            for item in itens:
                cur.execute(
                    """
                    INSERT INTO medicao_pasta_plano_acao
                    (dia, item, ocorrencia, causa, acao, quando, responsavel, created_by, registro_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        item.get("dia") or None,
                        item.get("item") or None,
                        item["ocorrencia"],
                        item.get("causa") or None,
                        item.get("acao") or None,
                        item.get("quando") or None,
                        item.get("responsavel") or None,
                        user_id,
                        registro_id,
                    ),
                )
        conn.commit()


def get_plano_by_registro_id(registro_id: int) -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT dia, item, ocorrencia, causa, acao, quando, responsavel
                FROM medicao_pasta_plano_acao
                WHERE registro_id = %s
                ORDER BY id
                """,
                (registro_id,),
            )
            return cur.fetchall()
