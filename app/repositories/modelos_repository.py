from psycopg.rows import dict_row

from app.extensions import get_db


def listar_codigos():
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT codigo FROM modelos ORDER BY codigo")
            return [r["codigo"] for r in (cur.fetchall() or [])]


def listar_modelos():
    """
    Lista completa para UI/API.
    IMPORTANTe: inclui 'linha' (antes faltava) — isso quebrava a API (/api/modelos)
    e, por consequência, a Home e a página de Modelos.
    """
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    codigo,
                    cliente,
                    setor,
                    linha,
                    meta_padrao,
                    tempo_montagem,
                    blank,
                    fase,
                    criado_em
                FROM modelos
                ORDER BY criado_em DESC NULLS LAST, codigo ASC
            """)
            return cur.fetchall() or []


def buscar_ultimo_modelo():
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT codigo
                FROM modelos
                ORDER BY criado_em DESC NULLS LAST
                LIMIT 1
            """)
            row = cur.fetchone()
            return row["codigo"] if row else None


def inserir(dados):
    """
    Observação importante:
    - No banco atual, tempo_montagem pode estar como INTEGER.
    - O frontend pode enviar decimal (ex.: "22.19") e isso quebra se tentar gravar direto.
    - Aqui convertemos via SQL: texto -> numeric -> int (trunca casas decimais).
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO modelos (
                    codigo,
                    cliente,
                    setor,
                    linha,
                    meta_padrao,
                    tempo_montagem,
                    blank,
                    fase
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    NULLIF(%s, '')::numeric,
                    NULLIF(%s, '')::numeric::int,
                    NULLIF(%s, '')::int,
                    %s
                )
            """, (
                dados["codigo"],
                dados["cliente"],
                dados["setor"],
                dados["linha"],
                dados["meta_padrao"],
                dados.get("tempo_montagem"),
                dados["blank"],
                dados["fase"]
            ))
        conn.commit()


def excluir(codigo, fase, linha):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM modelos WHERE codigo = %s AND fase = %s AND linha = %s",
                (codigo, fase, linha)
            )
        conn.commit()


def atualizar_meta(codigo, nova_meta):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE modelos SET meta_padrao = %s WHERE codigo = %s",
                (nova_meta, codigo)
            )
        conn.commit()


def atualizar(codigo, fase, linha, campos):
    """
    Casts por campo para evitar erros quando o frontend envia números como string/decimal.
    - meta_padrao: numeric
    - tempo_montagem: numeric -> int (trunca)
    - blank: int
    """
    casts = {
        "meta_padrao": "::numeric",
        "tempo_montagem": "::numeric::int",
        "blank": "::int",
    }

    sets = ", ".join(f"{k} = %s{casts.get(k, '')}" for k in campos)
    valores = list(campos.values()) + [codigo, fase, linha]

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE modelos
                SET {sets}
                WHERE codigo = %s AND fase = %s AND linha = %s
                """,
                valores
            )
        conn.commit()
