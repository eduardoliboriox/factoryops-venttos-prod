from app.extensions import get_db
from psycopg.rows import dict_row


def listar(data: str, turno: str = "", setor: str = "", linha: str = "") -> list:
    filtros = ["p.data = %s"]
    params  = [data]

    if turno:
        filtros.append("p.turno = %s")
        params.append(turno)
    if setor:
        filtros.append("p.setor = %s")
        params.append(setor)
    if linha:
        filtros.append("p.linha = %s")
        params.append(linha)

    where = " AND ".join(filtros)
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT
                    p.id, p.data, p.turno, p.setor, p.linha,
                    p.op_id, p.modelo, p.quantidade_planejada, p.taxa_horaria,
                    p.setup_min,
                    p.hora_inicio_prevista, p.hora_fim_prevista,
                    p.status, p.observacao, p.criado_por, p.criado_em,
                    co.numero_op,
                    co.descricao AS descricao_op,
                    (co.quantidade - co.produzido) AS saldo_op
                FROM planejamento p
                LEFT JOIN controle_ops co ON co.id = p.op_id
                WHERE {where}
                ORDER BY p.turno, p.linha, p.hora_inicio_prevista
            """, params)
            return cur.fetchall()


def buscar_por_id(planejamento_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT p.*, co.numero_op,
                       (co.quantidade - co.produzido) AS saldo_op
                FROM planejamento p
                LEFT JOIN controle_ops co ON co.id = p.op_id
                WHERE p.id = %s
            """, (planejamento_id,))
            return cur.fetchone()


def inserir(data: dict) -> int:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO planejamento (
                    data, turno, setor, linha, op_id, modelo,
                    quantidade_planejada, taxa_horaria, setup_min,
                    hora_inicio_prevista, hora_fim_prevista,
                    status, observacao, criado_por
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'PLANEJADO',%s,%s)
                RETURNING id
            """, (
                data["data"],
                data["turno"],
                data["setor"],
                data["linha"],
                data.get("op_id") or None,
                data["modelo"],
                data["quantidade_planejada"],
                data["taxa_horaria"],
                data.get("setup_min", 0),
                data["hora_inicio_prevista"],
                data.get("hora_fim_prevista") or None,
                data.get("observacao") or None,
                data.get("criado_por") or None,
            ))
            return cur.fetchone()["id"]


def atualizar(planejamento_id: int, data: dict) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE planejamento SET
                    op_id                = %s,
                    modelo               = %s,
                    quantidade_planejada = %s,
                    taxa_horaria         = %s,
                    setup_min            = %s,
                    hora_inicio_prevista = %s,
                    hora_fim_prevista    = %s,
                    observacao           = %s
                WHERE id = %s
            """, (
                data.get("op_id") or None,
                data["modelo"],
                data["quantidade_planejada"],
                data["taxa_horaria"],
                data.get("setup_min", 0),
                data["hora_inicio_prevista"],
                data.get("hora_fim_prevista") or None,
                data.get("observacao") or None,
                planejamento_id,
            ))


def atualizar_status(planejamento_id: int, status: str) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE planejamento SET status = %s WHERE id = %s",
                (status, planejamento_id),
            )


def excluir(planejamento_id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM planejamento WHERE id = %s", (planejamento_id,))


def listar_plano_de_voo(data: str, turno: str = "", setor: str = "", linha: str = "") -> list:
    filtros = ["p.data = %s"]
    params  = [data]
    if turno:
        filtros.append("p.turno = %s")
        params.append(turno)
    if setor:
        filtros.append("p.setor = %s")
        params.append(setor)
    if linha:
        filtros.append("p.linha = %s")
        params.append(linha)

    where = " AND ".join(filtros)
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT p.id, p.linha, p.setor, p.turno, p.modelo, p.op_id,
                       co.numero_op,
                       p.quantidade_planejada, p.taxa_horaria, p.setup_min,
                       p.hora_inicio_prevista, p.hora_fim_prevista, p.status
                FROM planejamento p
                LEFT JOIN controle_ops co ON co.id = p.op_id
                WHERE {where}
                ORDER BY p.linha, p.hora_inicio_prevista
            """, params)
            return cur.fetchall()


def familia_por_modelo(modelo: str) -> str | None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT familia FROM producao_coletada WHERE modelo = %s AND familia IS NOT NULL AND familia <> '' LIMIT 1",
                (modelo,)
            )
            row = cur.fetchone()
            return row["familia"] if row else None


def ops_abertas(setor: str = "") -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if setor:
                cur.execute("""
                    SELECT id, numero_op, produto, filial, setor,
                           quantidade, produzido,
                           (quantidade - produzido) AS saldo
                    FROM controle_ops
                    WHERE quantidade > produzido
                      AND (setor = %s OR setor IS NULL)
                    ORDER BY numero_op
                """, (setor,))
            else:
                cur.execute("""
                    SELECT id, numero_op, produto, filial, setor,
                           quantidade, produzido,
                           (quantidade - produzido) AS saldo
                    FROM controle_ops
                    WHERE quantidade > produzido
                    ORDER BY numero_op
                """)
            return cur.fetchall()


def turno_intervalos(turno: str) -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT hora_inicio, hora_fim
                FROM turno_config
                WHERE turno = %s
                ORDER BY ordem
            """, (turno,))
            return cur.fetchall()


def paradas_da_linha(setor: str, linha: str) -> list:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT hora_inicio, duracao_min, tipo, frequencia_dias
                FROM parada_config
                WHERE hora_inicio IS NOT NULL
                  AND (setor = %s OR setor IS NULL)
                  AND (linha = %s OR linha IS NULL)
                ORDER BY hora_inicio
            """, (setor, linha))
            return cur.fetchall()
