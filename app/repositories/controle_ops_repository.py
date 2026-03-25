from app.extensions import get_db
from psycopg.rows import dict_row


def listar(filial: str = "", status: str = "", setor: str = "") -> list:
    filtros = ["1=1"]
    params  = []

    if filial:
        filtros.append("filial = %s")
        params.append(filial)
    if setor:
        filtros.append("setor = %s")
        params.append(setor)
    if status == "aberta":
        filtros.append("quantidade > produzido")
    elif status == "concluida":
        filtros.append("quantidade <= produzido")

    where = " AND ".join(filtros)
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT
                    id, filial, numero_op, produto, descricao, armazem, setor, fase_modelo,
                    quantidade, produzido,
                    (quantidade - produzido) AS saldo,
                    pedido_venda, item_pedido_venda, criado_em
                FROM controle_ops
                WHERE {where}
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
