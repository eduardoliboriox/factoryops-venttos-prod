from app.extensions import get_db
from psycopg.rows import dict_row


def listar_pedidos(status: str = "", modelo: str = "", data_inicial: str = "", data_final: str = "",
                   order_by: str = "data_entrega") -> list:
    filtros = ["1=1"]
    params = []
    if status:
        filtros.append("p.status = %s")
        params.append(status)
    if modelo:
        filtros.append("p.modelo ILIKE %s")
        params.append(f"%{modelo}%")
    if data_inicial:
        filtros.append("p.data_entrega >= %s")
        params.append(data_inicial)
    if data_final:
        filtros.append("p.data_entrega <= %s")
        params.append(data_final)
    where = " AND ".join(filtros)
    order = "p.cliente ASC, p.data_entrega ASC" if order_by == "cliente" else "p.data_entrega ASC"
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT
                    p.*,
                    COALESCE((
                        SELECT SUM(a.quantidade)
                        FROM apontamento a
                        JOIN controle_ops co ON co.id = a.op_id
                        WHERE (a.modelo = p.modelo
                               OR p.modelo LIKE a.modelo || ' %%'
                               OR a.modelo LIKE p.modelo || ' %%')
                          AND co.setor = (
                              SELECT re.setor
                              FROM roteiro_etapas re
                              JOIN roteiro_modelos rm ON rm.roteiro_id = re.roteiro_id
                              JOIN roteiros r       ON r.id = rm.roteiro_id
                              WHERE (rm.modelo_codigo = p.modelo
                                     OR p.modelo LIKE rm.modelo_codigo || ' %%')
                                AND r.ativo = TRUE
                              ORDER BY re.ordem DESC
                              LIMIT 1
                          )
                    ), 0) AS produzido,
                    (
                        SELECT STRING_AGG(DISTINCT co.numero_op, ', ' ORDER BY co.numero_op)
                        FROM controle_ops co
                        WHERE co.produto = p.modelo
                           OR p.modelo LIKE co.produto || ' %%'
                    ) AS ops,
                    COALESCE((
                        SELECT SUM(e.quantidade) FROM entrega e WHERE e.pedido_id = p.id
                    ), 0) AS qtd_em_remessa,
                    COALESCE((
                        SELECT SUM(e.quantidade) FROM entrega e
                        WHERE e.pedido_id = p.id AND e.status = 'entregue'
                    ), 0) AS qtd_entregue,
                    (SELECT COUNT(*) FROM entrega e WHERE e.pedido_id = p.id) AS total_remessas,
                    p.local_entrega_id,
                    l.nome_local AS local_nome,
                    l.lat AS local_lat,
                    l.lng AS local_lng
                FROM pedido_cliente p
                LEFT JOIN local_entrega l ON l.id = p.local_entrega_id
                WHERE {where}
                ORDER BY {order}
            """, params)
            return cur.fetchall()


def buscar_pedido(pedido_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT p.*, l.nome_local AS local_nome, l.endereco AS local_endereco,
                       l.lat AS local_lat, l.lng AS local_lng
                FROM pedido_cliente p
                LEFT JOIN local_entrega l ON l.id = p.local_entrega_id
                WHERE p.id = %s
            """, (pedido_id,))
            return cur.fetchone()


def criar_pedido(numero_pedido: str, cliente: str, modelo: str, familia: str,
                 quantidade: int, data_pedido: str, data_entrega: str, observacao: str,
                 local_entrega_id: int | None = None) -> int:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO pedido_cliente
                    (numero_pedido, cliente, modelo, familia, quantidade, data_pedido, data_entrega,
                     observacao, local_entrega_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (numero_pedido, cliente, modelo, familia or None, quantidade,
                  data_pedido, data_entrega, observacao or None, local_entrega_id))
            return cur.fetchone()["id"]


def atualizar_pedido(pedido_id: int, numero_pedido: str, cliente: str, modelo: str, familia: str,
                     quantidade: int, data_pedido: str, data_entrega: str, observacao: str,
                     local_entrega_id: int | None = None) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE pedido_cliente SET
                    numero_pedido = %s, cliente = %s, modelo = %s, familia = %s,
                    quantidade = %s, data_pedido = %s, data_entrega = %s,
                    observacao = %s, local_entrega_id = %s, atualizado_em = NOW()
                WHERE id = %s
            """, (numero_pedido, cliente, modelo, familia or None,
                  quantidade, data_pedido, data_entrega, observacao or None,
                  local_entrega_id, pedido_id))


def excluir_pedido(pedido_id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM pedido_cliente WHERE id = %s", (pedido_id,))


def listar_entregas() -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    e.*,
                    p.numero_pedido, p.cliente, p.modelo, p.familia,
                    p.quantidade AS qtd_pedido, p.data_entrega AS data_entrega_prevista,
                    m.nome AS motorista_nome, m.telefone AS motorista_telefone,
                    COALESCE((
                        SELECT JSON_AGG(JSON_BUILD_OBJECT('id', eq.id, 'nome', eq.nome, 'tipo', eq.tipo))
                        FROM entrega_equipe ee
                        JOIN equipe_entrega eq ON eq.id = ee.membro_id
                        WHERE ee.entrega_id = e.id
                    ), '[]'::json) AS membros
                FROM entrega e
                JOIN pedido_cliente p ON p.id = e.pedido_id
                LEFT JOIN equipe_entrega m ON m.id = e.motorista_id
                ORDER BY e.criado_em DESC
            """)
            return cur.fetchall()


def listar_remessas_pedido(pedido_id: int) -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    e.id,
                    e.quantidade,
                    e.nota_fiscal,
                    e.status,
                    e.data_saida,
                    e.data_entrega_real,
                    e.criado_em,
                    m.nome AS motorista_nome
                FROM entrega e
                LEFT JOIN equipe_entrega m ON m.id = e.motorista_id
                WHERE e.pedido_id = %s
                ORDER BY e.criado_em ASC
            """, (pedido_id,))
            return cur.fetchall()


def buscar_entrega(entrega_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    e.*,
                    p.numero_pedido, p.cliente, p.modelo, p.familia,
                    p.quantidade AS qtd_pedido, p.data_entrega AS data_entrega_prevista,
                    m.nome AS motorista_nome, m.telefone AS motorista_telefone,
                    l.nome_local AS local_nome, l.endereco AS local_endereco,
                    l.lat AS local_lat, l.lng AS local_lng
                FROM entrega e
                JOIN pedido_cliente p ON p.id = e.pedido_id
                LEFT JOIN equipe_entrega m ON m.id = e.motorista_id
                LEFT JOIN local_entrega l ON l.id = p.local_entrega_id
                WHERE e.id = %s
            """, (entrega_id,))
            return cur.fetchone()


def soma_remessas_pedido(pedido_id: int) -> int:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT COALESCE(SUM(quantidade), 0) AS total FROM entrega WHERE pedido_id = %s",
                (pedido_id,)
            )
            return int(cur.fetchone()["total"])


def criar_entrega(pedido_id: int, quantidade: int, nota_fiscal: str) -> int:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO entrega (pedido_id, quantidade, nota_fiscal)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (pedido_id, quantidade, nota_fiscal or None))
            entrega_id = cur.fetchone()["id"]
            cur.execute(
                "UPDATE pedido_cliente SET status = 'em_producao', atualizado_em = NOW() WHERE id = %s AND status = 'aberto'",
                (pedido_id,)
            )
            return entrega_id


def atualizar_status_entrega(entrega_id: int, status: str,
                              nota_fiscal: str | None, motorista_id: int | None) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            updates = ["status = %s", "atualizado_em = NOW()"]
            params: list = [status]
            if nota_fiscal is not None:
                updates.append("nota_fiscal = %s")
                params.append(nota_fiscal)
            if motorista_id is not None:
                updates.append("motorista_id = %s")
                params.append(motorista_id)
            if status == "em_transito":
                updates.append("data_saida = NOW()")
            if status == "entregue":
                updates.append("data_entrega_real = NOW()")
            params.append(entrega_id)
            cur.execute(f"UPDATE entrega SET {', '.join(updates)} WHERE id = %s", params)
            if status == "entregue":
                cur.execute("""
                    UPDATE pedido_cliente SET status = 'entregue', atualizado_em = NOW()
                    WHERE id = (SELECT pedido_id FROM entrega WHERE id = %s)
                      AND quantidade <= (
                          SELECT COALESCE(SUM(e2.quantidade), 0)
                          FROM entrega e2
                          WHERE e2.pedido_id = (SELECT pedido_id FROM entrega WHERE id = %s)
                            AND (e2.id = %s OR e2.status = 'entregue')
                      )
                """, (entrega_id, entrega_id, entrega_id))


def atualizar_localizacao(entrega_id: int, lat: float, lng: float) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE entrega SET lat = %s, lng = %s, localizacao_em = NOW()
                WHERE id = %s
            """, (lat, lng, entrega_id))


def listar_equipe(tipo: str = "") -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if tipo:
                cur.execute(
                    "SELECT * FROM equipe_entrega WHERE ativo = TRUE AND tipo = %s ORDER BY nome",
                    (tipo,)
                )
            else:
                cur.execute(
                    "SELECT * FROM equipe_entrega WHERE ativo = TRUE ORDER BY tipo, nome"
                )
            return cur.fetchall()


def criar_membro_equipe(nome: str, tipo: str, telefone: str) -> int:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO equipe_entrega (nome, tipo, telefone)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (nome, tipo, telefone or None))
            return cur.fetchone()["id"]


def desativar_membro_equipe(membro_id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE equipe_entrega SET ativo = FALSE WHERE id = %s", (membro_id,))


def sincronizar_equipe_entrega(entrega_id: int, membro_ids: list[int]) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM entrega_equipe WHERE entrega_id = %s", (entrega_id,))
            for membro_id in membro_ids:
                cur.execute(
                    "INSERT INTO entrega_equipe (entrega_id, membro_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (entrega_id, membro_id)
                )


def resumo_apontamento_logistica(data: str) -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    a.data,
                    a.turno,
                    a.modelo,
                    a.linha,
                    SUM(a.quantidade) AS quantidade,
                    STRING_AGG(DISTINCT co.numero_op, ', ' ORDER BY co.numero_op) AS ops
                FROM apontamento a
                LEFT JOIN controle_ops co ON co.id = a.op_id
                WHERE a.data = %s
                GROUP BY a.data, a.turno, a.modelo, a.linha
                ORDER BY a.turno, a.modelo
            """, (data,))
            return cur.fetchall()
