from app.extensions import get_db


def listar_codigos():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT codigo FROM modelos ORDER BY codigo")
            return [r["codigo"] for r in cur.fetchall()]


def listar_modelos():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    codigo,
                    cliente,
                    setor,
                    meta_padrao,
                    tempo_montagem,
                    blank,
                    fase,
                    criado_em
                FROM modelos
            """)
            return cur.fetchall()


def buscar_ultimo_modelo():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT codigo
                FROM modelos
                ORDER BY criado_em DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            return row["codigo"] if row else None


def inserir(dados):
    """
    Observação importante:
    - No banco atual, tempo_montagem está como INTEGER.
    - O frontend pode enviar decimal (ex.: "55.86") e isso quebra se tentar gravar direto.
    - Aqui convertemos via SQL: texto -> numeric -> int (trunca casas decimais).
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO modelos (
                    codigo,
                    cliente,
                    setor,
                    meta_padrao,
                    tempo_montagem,
                    blank,
                    fase
                )
                VALUES (
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
                dados["meta_padrao"],
                dados["tempo_montagem"],
                dados["blank"],
                dados["fase"]
            ))
        conn.commit()


def excluir(codigo, fase):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM modelos WHERE codigo = %s AND fase = %s",
                (codigo, fase)
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


def atualizar(codigo, fase, campos):
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
    valores = list(campos.values()) + [codigo, fase]

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE modelos
                SET {sets}
                WHERE codigo = %s AND fase = %s
                """,
                valores
            )
        conn.commit()
