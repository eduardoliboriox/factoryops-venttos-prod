from app.extensions import get_db
from psycopg.rows import dict_row


def listar_agrupado(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "",
                    hora_inicio_turno=None, hora_fim_turno=None) -> list:
    if hora_inicio_turno is not None and hora_fim_turno is not None:
        filtros = [
            "pc.turno = %s AND ("
            "(pc.data BETWEEN %s AND %s AND pc.hora_inicio::time >= %s)"
            " OR "
            "(pc.data BETWEEN %s::date + INTERVAL '1 day' AND %s::date + INTERVAL '1 day'"
            " AND pc.hora_inicio::time <= %s)"
            ")"
        ]
        params = [turno, data_inicial, data_final, hora_inicio_turno,
                  data_inicial, data_final, hora_fim_turno]
    else:
        filtros = ["pc.data BETWEEN %s AND %s"]
        params  = [data_inicial, data_final]
        if turno:
            filtros.append("pc.turno = %s")
            params.append(turno)

    if setor:
        filtros.append("pc.setor = %s")
        params.append(setor)
    if linha:
        filtros.append("pc.linha = %s")
        params.append(linha)

    where = " AND ".join(filtros)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                WITH agrupado AS (
                    SELECT
                        pc.data, pc.turno, pc.setor, pc.linha, pc.modelo,
                        MAX(pc.familia)       AS familia,
                        SUM(pc.producao_real) AS producao_total
                    FROM producao_coletada pc
                    WHERE {where}
                    GROUP BY pc.data, pc.turno, pc.setor, pc.linha, pc.modelo
                )
                SELECT
                    g.data, g.turno, g.setor, g.linha, g.modelo,
                    g.familia, g.producao_total,
                    -- vínculo genérico (sem fase — usado para PTH, IM, PA, VTT)
                    a_gen.id            AS ap_id,
                    a_gen.op_id         AS ap_op_id,
                    a_gen.quantidade    AS ap_quantidade,
                    a_gen.lote          AS ap_lote,
                    co_gen.numero_op    AS ap_numero_op,
                    co_gen.produto      AS ap_produto,
                    (co_gen.quantidade - co_gen.produzido) AS ap_saldo,
                    -- vínculo SMD TOP
                    a_top.id            AS top_id,
                    a_top.op_id         AS top_op_id,
                    a_top.lote          AS top_lote,
                    co_top.numero_op    AS top_numero_op,
                    (co_top.quantidade - co_top.produzido) AS top_saldo,
                    -- vínculo SMD BOTTOM
                    a_bot.id            AS bot_id,
                    a_bot.op_id         AS bot_op_id,
                    a_bot.lote          AS bot_lote,
                    co_bot.numero_op    AS bot_numero_op,
                    (co_bot.quantidade - co_bot.produzido) AS bot_saldo
                FROM agrupado g
                LEFT JOIN apontamento a_gen ON (
                    a_gen.data   = g.data   AND
                    a_gen.turno  = g.turno  AND
                    a_gen.modelo = g.modelo AND
                    a_gen.linha  = g.linha  AND
                    a_gen.fase IS NULL
                )
                LEFT JOIN controle_ops co_gen ON co_gen.id = a_gen.op_id
                LEFT JOIN apontamento a_top ON (
                    a_top.data   = g.data   AND
                    a_top.turno  = g.turno  AND
                    a_top.modelo = g.modelo AND
                    a_top.linha  = g.linha  AND
                    a_top.fase   = 'TOP'
                )
                LEFT JOIN controle_ops co_top ON co_top.id = a_top.op_id
                LEFT JOIN apontamento a_bot ON (
                    a_bot.data   = g.data   AND
                    a_bot.turno  = g.turno  AND
                    a_bot.modelo = g.modelo AND
                    a_bot.linha  = g.linha  AND
                    a_bot.fase   = 'BOTTOM'
                )
                LEFT JOIN controle_ops co_bot ON co_bot.id = a_bot.op_id
                ORDER BY g.data DESC, g.turno, g.setor, g.linha, g.modelo
            """, params)
            return cur.fetchall()


def ops_abertas(setor: str = "") -> list:
    params = []
    setor_where = ""
    if setor:
        setor_where = "AND (co.setor = %s OR co.setor IS NULL)"
        params.append(setor)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT id, numero_op, produto, filial, setor, fase_modelo,
                       quantidade, produzido, saldo, top_feito, bottom_feito
                FROM (
                    SELECT
                        co.id, co.numero_op, co.produto, co.filial, co.setor, co.fase_modelo,
                        co.quantidade, co.produzido,
                        COALESCE(SUM(CASE WHEN a.fase = 'TOP'    THEN a.quantidade ELSE 0 END), 0) AS top_feito,
                        COALESCE(SUM(CASE WHEN a.fase = 'BOTTOM' THEN a.quantidade ELSE 0 END), 0) AS bottom_feito,
                        CASE WHEN co.fase_modelo = 'AMBAS' THEN
                            co.quantidade - LEAST(
                                COALESCE(SUM(CASE WHEN a.fase = 'TOP'    THEN a.quantidade ELSE 0 END), 0),
                                COALESCE(SUM(CASE WHEN a.fase = 'BOTTOM' THEN a.quantidade ELSE 0 END), 0)
                            )
                        ELSE (co.quantidade - co.produzido)
                        END AS saldo
                    FROM controle_ops co
                    LEFT JOIN apontamento a ON a.op_id = co.id
                    WHERE 1=1 {setor_where}
                    GROUP BY co.id, co.numero_op, co.produto, co.filial, co.setor,
                             co.fase_modelo, co.quantidade, co.produzido
                ) sub
                WHERE saldo > 0
                ORDER BY numero_op
            """, params)
            return cur.fetchall()


def buscar_op_para_vincular(op_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    co.id, co.produto, co.fase_modelo, co.quantidade,
                    COALESCE(SUM(CASE WHEN a.fase = 'TOP'    THEN a.quantidade ELSE 0 END), 0) AS top_feito,
                    COALESCE(SUM(CASE WHEN a.fase = 'BOTTOM' THEN a.quantidade ELSE 0 END), 0) AS bottom_feito,
                    CASE WHEN co.fase_modelo = 'AMBAS' THEN
                        co.quantidade - LEAST(
                            COALESCE(SUM(CASE WHEN a.fase = 'TOP'    THEN a.quantidade ELSE 0 END), 0),
                            COALESCE(SUM(CASE WHEN a.fase = 'BOTTOM' THEN a.quantidade ELSE 0 END), 0)
                        )
                    ELSE (co.quantidade - co.produzido)
                    END AS saldo
                FROM controle_ops co
                LEFT JOIN apontamento a ON a.op_id = co.id
                WHERE co.id = %s
                GROUP BY co.id, co.produto, co.fase_modelo, co.quantidade, co.produzido
            """, (op_id,))
            return cur.fetchone()


def vincular(data: str, turno: str, modelo: str, linha: str, op_id: int, quantidade: int,
             fase: str = None, lote: str = None) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO apontamento (op_id, data, turno, modelo, linha, quantidade, fase, lote)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (op_id, data, turno, modelo, linha, quantidade, fase or None, lote or None))
            cur.execute("SELECT fase_modelo FROM controle_ops WHERE id = %s", (op_id,))
            op_row = cur.fetchone()
            fase_modelo = op_row["fase_modelo"] if op_row else None
            if fase_modelo == "AMBAS":
                cur.execute("""
                    UPDATE controle_ops SET produzido = (
                        SELECT LEAST(
                            COALESCE(SUM(CASE WHEN fase = 'TOP'    THEN quantidade ELSE 0 END), 0),
                            COALESCE(SUM(CASE WHEN fase = 'BOTTOM' THEN quantidade ELSE 0 END), 0)
                        )
                        FROM apontamento WHERE op_id = %s
                    ) WHERE id = %s
                """, (op_id, op_id))
            else:
                cur.execute("""
                    UPDATE controle_ops SET produzido = produzido + %s WHERE id = %s
                """, (quantidade, op_id))


def desvincular(apontamento_id: int) -> None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT op_id, quantidade FROM apontamento WHERE id = %s", (apontamento_id,))
            row = cur.fetchone()
            if not row:
                return
            cur.execute("SELECT fase_modelo FROM controle_ops WHERE id = %s", (row["op_id"],))
            op_row = cur.fetchone()
            fase_modelo = op_row["fase_modelo"] if op_row else None
            cur.execute("DELETE FROM apontamento WHERE id = %s", (apontamento_id,))
            if fase_modelo == "AMBAS":
                cur.execute("""
                    UPDATE controle_ops SET produzido = (
                        SELECT LEAST(
                            COALESCE(SUM(CASE WHEN fase = 'TOP'    THEN quantidade ELSE 0 END), 0),
                            COALESCE(SUM(CASE WHEN fase = 'BOTTOM' THEN quantidade ELSE 0 END), 0)
                        )
                        FROM apontamento WHERE op_id = %s
                    ) WHERE id = %s
                """, (row["op_id"], row["op_id"]))
            else:
                cur.execute("""
                    UPDATE controle_ops SET produzido = GREATEST(0, produzido - %s) WHERE id = %s
                """, (row["quantidade"], row["op_id"]))


def fila_producao() -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT setor, id, numero_op, produto, descricao, fase_modelo,
                       quantidade, produzido, saldo,
                       top_feito, bottom_feito, aguardando_bottom, aguardando_top
                FROM (
                    SELECT
                        co.setor, co.id, co.numero_op, co.produto, co.descricao,
                        co.fase_modelo, co.quantidade, co.produzido,
                        COALESCE(SUM(CASE WHEN a.fase = 'TOP'    THEN a.quantidade ELSE 0 END), 0) AS top_feito,
                        COALESCE(SUM(CASE WHEN a.fase = 'BOTTOM' THEN a.quantidade ELSE 0 END), 0) AS bottom_feito,
                        GREATEST(0,
                            COALESCE(SUM(CASE WHEN a.fase = 'TOP'    THEN a.quantidade ELSE 0 END), 0) -
                            COALESCE(SUM(CASE WHEN a.fase = 'BOTTOM' THEN a.quantidade ELSE 0 END), 0)
                        ) AS aguardando_bottom,
                        GREATEST(0,
                            COALESCE(SUM(CASE WHEN a.fase = 'BOTTOM' THEN a.quantidade ELSE 0 END), 0) -
                            COALESCE(SUM(CASE WHEN a.fase = 'TOP'    THEN a.quantidade ELSE 0 END), 0)
                        ) AS aguardando_top,
                        CASE WHEN co.fase_modelo = 'AMBAS' THEN
                            co.quantidade - LEAST(
                                COALESCE(SUM(CASE WHEN a.fase = 'TOP'    THEN a.quantidade ELSE 0 END), 0),
                                COALESCE(SUM(CASE WHEN a.fase = 'BOTTOM' THEN a.quantidade ELSE 0 END), 0)
                            )
                        ELSE (co.quantidade - co.produzido)
                        END AS saldo
                    FROM controle_ops co
                    LEFT JOIN apontamento a ON a.op_id = co.id
                    GROUP BY co.setor, co.id, co.numero_op, co.produto, co.descricao,
                             co.fase_modelo, co.quantidade, co.produzido
                ) sub
                WHERE saldo > 0
                ORDER BY setor NULLS LAST, numero_op
            """)
            return cur.fetchall()
