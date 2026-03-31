from app.extensions import get_db
from psycopg.rows import dict_row


def listar(filial: str = "", status: str = "", setor: str = "") -> list:
    inner_filtros = ["1=1"]
    params        = []

    if filial:
        inner_filtros.append("co.filial = %s")
        params.append(filial)
    if setor:
        inner_filtros.append("co.setor = %s")
        params.append(setor)

    inner_where = " AND ".join(inner_filtros)

    status_having = ""
    if status == "aberta":
        status_having = "WHERE saldo > 0"
    elif status == "concluida":
        status_having = "WHERE saldo <= 0"

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT id, filial, numero_op, produto, descricao, armazem, setor, fase_modelo,
                       quantidade, produzido, saldo, pedido_venda, item_pedido_venda, criado_em
                FROM (
                    SELECT
                        co.id, co.filial, co.numero_op, co.produto, co.descricao,
                        co.armazem, co.setor, co.fase_modelo, co.quantidade, co.produzido,
                        co.pedido_venda, co.item_pedido_venda, co.criado_em,
                        CASE WHEN co.fase_modelo = 'AMBAS' THEN
                            co.quantidade - LEAST(
                                COALESCE(SUM(CASE WHEN a.fase = 'TOP'    THEN a.quantidade ELSE 0 END), 0),
                                COALESCE(SUM(CASE WHEN a.fase = 'BOTTOM' THEN a.quantidade ELSE 0 END), 0)
                            )
                        ELSE (co.quantidade - co.produzido)
                        END AS saldo
                    FROM controle_ops co
                    LEFT JOIN apontamento a ON a.op_id = co.id
                    WHERE {inner_where}
                    GROUP BY co.id, co.filial, co.numero_op, co.produto, co.descricao,
                             co.armazem, co.setor, co.fase_modelo, co.quantidade, co.produzido,
                             co.pedido_venda, co.item_pedido_venda, co.criado_em
                ) sub
                {status_having}
                ORDER BY criado_em DESC
            """, params)
            return cur.fetchall()


def buscar_por_id(op_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, filial, numero_op, produto, descricao, armazem, setor, fase_modelo,
                       quantidade, produzido, pedido_venda, item_pedido_venda
                FROM controle_ops WHERE id = %s
            """, (op_id,))
            return cur.fetchone()


def inserir(data: dict) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO controle_ops (
                    filial, numero_op, produto, descricao, armazem, setor, fase_modelo,
                    quantidade, pedido_venda, item_pedido_venda
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data["filial"],
                data["numero_op"],
                data["produto"],
                data.get("descricao") or None,
                data.get("armazem") or None,
                data.get("setor") or None,
                data.get("fase_modelo") or None,
                data["quantidade"],
                data.get("pedido_venda") or None,
                data.get("item_pedido_venda") or None,
            ))


def inserir_lote(registros: list[dict]) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            for data in registros:
                cur.execute("""
                    INSERT INTO controle_ops (
                        filial, numero_op, produto, descricao, armazem, setor, fase_modelo,
                        quantidade, pedido_venda, item_pedido_venda
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data["filial"],
                    data["numero_op"],
                    data["produto"],
                    data.get("descricao") or None,
                    data.get("armazem") or None,
                    data.get("setor") or None,
                    data.get("fase_modelo") or None,
                    data["quantidade"],
                    data.get("pedido_venda") or None,
                    data.get("item_pedido_venda") or None,
                ))


def atualizar(op_id: int, data: dict) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE controle_ops SET
                    filial            = %s,
                    numero_op         = %s,
                    produto           = %s,
                    descricao         = %s,
                    armazem           = %s,
                    setor             = %s,
                    fase_modelo       = %s,
                    quantidade        = %s,
                    pedido_venda      = %s,
                    item_pedido_venda = %s
                WHERE id = %s
            """, (
                data["filial"],
                data["numero_op"],
                data["produto"],
                data.get("descricao") or None,
                data.get("armazem") or None,
                data.get("setor") or None,
                data.get("fase_modelo") or None,
                data["quantidade"],
                data.get("pedido_venda") or None,
                data.get("item_pedido_venda") or None,
                op_id,
            ))


def excluir(op_id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM controle_ops WHERE id = %s", (op_id,))


def filiais_disponiveis() -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT DISTINCT filial FROM controle_ops ORDER BY filial")
            return [r["filial"] for r in cur.fetchall()]


def buscar_familia_op(base: str) -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, numero_op, setor, produzido
                FROM controle_ops
                WHERE numero_op LIKE %s
                  AND RIGHT(numero_op, 2) IN ('01', '02', '03', '04')
                ORDER BY numero_op
            """, (base + '__',))
            return cur.fetchall()
