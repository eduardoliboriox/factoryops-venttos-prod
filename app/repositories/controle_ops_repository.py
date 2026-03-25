from app.extensions import get_db
from psycopg.rows import dict_row


def listar(filial: str = "", status: str = "") -> list:
    filtros = ["1=1"]
    params  = []

    if filial:
        filtros.append("filial = %s")
        params.append(filial)
    if status == "aberta":
        filtros.append("quantidade > produzido")
    elif status == "concluida":
        filtros.append("quantidade <= produzido")

    where = " AND ".join(filtros)
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT
                    id, filial, numero_op, produto, descricao, armazem,
                    quantidade, produzido,
                    (quantidade - produzido) AS saldo,
                    pedido_venda, item_pedido_venda, criado_em
                FROM controle_ops
                WHERE {where}
                ORDER BY criado_em DESC
            """, params)
            return cur.fetchall()


def inserir(data: dict) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO controle_ops (
                    filial, numero_op, produto, descricao, armazem,
                    quantidade, pedido_venda, item_pedido_venda
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data["filial"],
                data["numero_op"],
                data["produto"],
                data.get("descricao") or None,
                data.get("armazem") or None,
                data["quantidade"],
                data.get("pedido_venda") or None,
                data.get("item_pedido_venda") or None,
            ))


def filiais_disponiveis() -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT DISTINCT filial FROM controle_ops ORDER BY filial")
            return [r["filial"] for r in cur.fetchall()]
