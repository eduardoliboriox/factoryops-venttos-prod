from app.extensions import get_db
from psycopg.rows import dict_row


def listar(data_inicial: str = "", data_final: str = "", turno: str = "",
           status: str = "", criado_por: str = "") -> list:
    filtros = ["1=1"]
    params  = []

    if data_inicial:
        filtros.append("r.data >= %s")
        params.append(data_inicial)
    if data_final:
        filtros.append("r.data <= %s")
        params.append(data_final)
    if turno:
        filtros.append("r.turno = %s")
        params.append(turno)
    if status:
        filtros.append("r.status = %s")
        params.append(status)
    if criado_por:
        filtros.append("r.criado_por = %s")
        params.append(criado_por)

    where = " AND ".join(filtros)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"""
                SELECT r.id, r.data, r.turno, r.status, r.criado_em, r.criado_por,
                       COUNT(DISTINCT l.id) AS num_linhas
                FROM resumo_producao r
                LEFT JOIN resumo_producao_linha l ON l.resumo_id = r.id
                WHERE {where}
                GROUP BY r.id
                ORDER BY r.data DESC, r.turno
            """, params)
            return cur.fetchall()


def buscar_por_id(resumo_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, data, turno, status, criado_em, criado_por
                FROM resumo_producao WHERE id = %s
            """, (resumo_id,))
            resumo = cur.fetchone()
            if not resumo:
                return None

            cur.execute("""
                SELECT id, nome_linha, observacao, ordem
                FROM resumo_producao_linha
                WHERE resumo_id = %s
                ORDER BY ordem, id
            """, (resumo_id,))
            linhas = cur.fetchall()

            for linha in linhas:
                cur.execute("""
                    SELECT id, codigo_modelo, produto, ops, produzido_top, produzido_bot, observacao, ordem
                    FROM resumo_producao_modelo
                    WHERE linha_id = %s
                    ORDER BY ordem, id
                """, (linha["id"],))
                linha["modelos"] = cur.fetchall()

            resumo["linhas"] = linhas
            return resumo


def inserir(data: dict) -> int:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO resumo_producao (data, turno, status, criado_por)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (data["data"], data["turno"], data["status"], data.get("criado_por")))
            resumo_id = cur.fetchone()["id"]

            for i, linha in enumerate(data.get("linhas", [])):
                cur.execute("""
                    INSERT INTO resumo_producao_linha (resumo_id, nome_linha, observacao, ordem)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (resumo_id, linha["nome_linha"], linha.get("observacao") or None, i))
                linha_id = cur.fetchone()["id"]

                for j, modelo in enumerate(linha.get("modelos", [])):
                    cur.execute("""
                        INSERT INTO resumo_producao_modelo
                            (linha_id, codigo_modelo, produto, ops, produzido_top, produzido_bot, observacao, ordem)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        linha_id,
                        modelo.get("codigo_modelo") or None,
                        modelo.get("produto") or None,
                        modelo.get("ops") or None,
                        modelo.get("produzido_top") or 0,
                        modelo.get("produzido_bot") or 0,
                        modelo.get("observacao") or None,
                        j,
                    ))

            return resumo_id


def atualizar(resumo_id: int, data: dict) -> None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                UPDATE resumo_producao
                SET data = %s, turno = %s, status = %s
                WHERE id = %s
            """, (data["data"], data["turno"], data["status"], resumo_id))

            cur.execute("""
                DELETE FROM resumo_producao_linha WHERE resumo_id = %s
            """, (resumo_id,))

            for i, linha in enumerate(data.get("linhas", [])):
                cur.execute("""
                    INSERT INTO resumo_producao_linha (resumo_id, nome_linha, observacao, ordem)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (resumo_id, linha["nome_linha"], linha.get("observacao") or None, i))
                linha_id = cur.fetchone()["id"]

                for j, modelo in enumerate(linha.get("modelos", [])):
                    cur.execute("""
                        INSERT INTO resumo_producao_modelo
                            (linha_id, codigo_modelo, produto, ops, produzido_top, produzido_bot, observacao, ordem)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        linha_id,
                        modelo.get("codigo_modelo") or None,
                        modelo.get("produto") or None,
                        modelo.get("ops") or None,
                        modelo.get("produzido_top") or 0,
                        modelo.get("produzido_bot") or 0,
                        modelo.get("observacao") or None,
                        j,
                    ))


def excluir(resumo_id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM resumo_producao WHERE id = %s", (resumo_id,))
