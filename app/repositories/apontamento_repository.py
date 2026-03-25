from app.extensions import get_db
from psycopg.rows import dict_row


def listar_agrupado(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "") -> list:
    filtros = ["pc.data BETWEEN %s AND %s"]
    params  = [data_inicial, data_final]

    if setor:
        filtros.append("pc.setor = %s")
        params.append(setor)
    if linha:
        filtros.append("pc.linha = %s")
        params.append(linha)
    if turno:
        filtros.append("pc.turno = %s")
        params.append(turno)

    where = " AND ".join(filtros)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                WITH agrupado AS (
                    SELECT
                        data, turno, setor, linha, modelo,
                        MAX(familia)       AS familia,
                        SUM(producao_real) AS producao_total
                    FROM producao_coletada
                    WHERE {where}
                    GROUP BY data, turno, setor, linha, modelo
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
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if setor:
                cur.execute("""
                    SELECT id, numero_op, produto, filial, setor, quantidade, produzido,
                           (quantidade - produzido) AS saldo
                    FROM controle_ops
                    WHERE quantidade > produzido
                      AND (setor = %s OR setor IS NULL)
                    ORDER BY numero_op
                """, (setor,))
            else:
                cur.execute("""
                    SELECT id, numero_op, produto, filial, setor, quantidade, produzido,
                           (quantidade - produzido) AS saldo
                    FROM controle_ops
                    WHERE quantidade > produzido
                    ORDER BY numero_op
                """)
            return cur.fetchall()


def vincular(data: str, turno: str, modelo: str, linha: str, op_id: int, quantidade: int,
             fase: str = None, lote: str = None) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO apontamento (op_id, data, turno, modelo, linha, quantidade, fase, lote)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (op_id, data, turno, modelo, linha, quantidade, fase or None, lote or None))
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
            cur.execute("""
                UPDATE controle_ops SET produzido = GREATEST(0, produzido - %s) WHERE id = %s
            """, (row["quantidade"], row["op_id"]))
            cur.execute("DELETE FROM apontamento WHERE id = %s", (apontamento_id,))
