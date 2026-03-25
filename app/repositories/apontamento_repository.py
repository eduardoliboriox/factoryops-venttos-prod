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
                SELECT
                    pc.data,
                    pc.turno,
                    pc.setor,
                    pc.linha,
                    pc.modelo,
                    MAX(pc.familia)          AS familia,
                    SUM(pc.producao_real)    AS producao_total,
                    a.id                     AS apontamento_id,
                    a.op_id,
                    a.quantidade             AS apontamento_quantidade,
                    co.numero_op,
                    co.produto,
                    co.quantidade            AS op_quantidade,
                    co.produzido             AS op_produzido,
                    (co.quantidade - co.produzido) AS op_saldo
                FROM producao_coletada pc
                LEFT JOIN apontamento a ON (
                    a.data   = pc.data  AND
                    a.turno  = pc.turno AND
                    a.modelo = pc.modelo AND
                    a.linha  = pc.linha
                )
                LEFT JOIN controle_ops co ON co.id = a.op_id
                WHERE {where}
                GROUP BY
                    pc.data, pc.turno, pc.setor, pc.linha, pc.modelo,
                    a.id, a.op_id, a.quantidade,
                    co.numero_op, co.produto, co.quantidade, co.produzido
                ORDER BY pc.data DESC, pc.turno, pc.setor, pc.linha, pc.modelo
            """, params)
            return cur.fetchall()


def ops_abertas() -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, numero_op, produto, filial, quantidade, produzido,
                       (quantidade - produzido) AS saldo
                FROM controle_ops
                WHERE quantidade > produzido
                ORDER BY numero_op
            """)
            return cur.fetchall()


def vincular(data: str, turno: str, modelo: str, linha: str, op_id: int, quantidade: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO apontamento (op_id, data, turno, modelo, linha, quantidade)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (op_id, data, turno, modelo, linha, quantidade))
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
