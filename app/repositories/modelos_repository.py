from __future__ import annotations

from typing import Optional

from psycopg.rows import dict_row
from psycopg import sql

from app.extensions import get_db


_LINHA_COL_CACHE: Optional[str] = None
_LINHA_COL_CHECKED: bool = False


def _resolve_linha_column() -> Optional[str]:
    """
    Detecta (uma única vez) qual coluna do banco representa "linha" na tabela modelos.
    Suporta bancos legados (sem coluna linha) e bancos novos (com linha ou nome alternativo).
    """
    global _LINHA_COL_CACHE, _LINHA_COL_CHECKED

    if _LINHA_COL_CHECKED:
        return _LINHA_COL_CACHE

    candidates = [
        "linha",         
        "line",          
        "linha_smd",     
        "linha_padrao",
        "linha_nome",
        "linha_producao",
    ]

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'modelos'
                """
            )
            cols = {r["column_name"] for r in (cur.fetchall() or [])}

    for c in candidates:
        if c in cols:
            _LINHA_COL_CACHE = c
            _LINHA_COL_CHECKED = True
            return _LINHA_COL_CACHE

    _LINHA_COL_CACHE = None
    _LINHA_COL_CHECKED = True
    return None


def listar_codigos():
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT codigo FROM modelos ORDER BY codigo")
            return [r["codigo"] for r in (cur.fetchall() or [])]


def listar_modelos():
    """
    Lista completa para UI/API.
    Compatível com schema legado que não tem coluna de "linha".
    - Se existir uma coluna equivalente: retorna como alias 'linha'
    - Se não existir: retorna 'linha' como NULL
    """
    linha_col = _resolve_linha_column()

    if linha_col:
        linha_select = sql.SQL("{} AS linha").format(sql.Identifier(linha_col))
    else:
        linha_select = sql.SQL("NULL::text AS linha")

    query = sql.SQL("""
        SELECT
            codigo,
            cliente,
            setor,
            {linha_select},
            meta_padrao,
            tempo_montagem,
            blank,
            fase,
            criado_em
        FROM modelos
        ORDER BY criado_em DESC NULLS LAST, codigo ASC
    """).format(linha_select=linha_select)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query)
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
    Compatível com banco com/sem coluna de linha.

    Importante:
    - tempo_montagem NÃO deve ser forçado para int (precisa manter 2 casas decimais).
    - espera-se que no banco a coluna esteja como NUMERIC(10,2).
    """
    linha_col = _resolve_linha_column()

    base_cols = [
        "codigo",
        "cliente",
        "setor",
        "meta_padrao",
        "tempo_montagem",
        "blank",
        "fase",
    ]
    base_vals = [
        dados["codigo"],
        dados["cliente"],
        dados["setor"],
        dados["meta_padrao"],
        dados.get("tempo_montagem"),
        dados["blank"],
        dados["fase"],
    ]

    if linha_col:
        cols = ["codigo", "cliente", "setor", linha_col, "meta_padrao", "tempo_montagem", "blank", "fase"]
        vals = [
            dados["codigo"],
            dados["cliente"],
            dados["setor"],
            dados.get("linha"),
            dados["meta_padrao"],
            dados.get("tempo_montagem"),
            dados["blank"],
            dados["fase"],
        ]

        query = sql.SQL("""
            INSERT INTO modelos ({cols})
            VALUES (
                %s, %s, %s, %s,
                NULLIF(%s, '')::numeric,
                NULLIF(%s, '')::numeric,
                NULLIF(%s, '')::int,
                %s
            )
        """).format(cols=sql.SQL(", ").join(sql.Identifier(c) for c in cols))

        params = tuple(vals)

    else:
        query = sql.SQL("""
            INSERT INTO modelos ({cols})
            VALUES (
                %s, %s, %s,
                NULLIF(%s, '')::numeric,
                NULLIF(%s, '')::numeric,
                NULLIF(%s, '')::int,
                %s
            )
        """).format(cols=sql.SQL(", ").join(sql.Identifier(c) for c in base_cols))

        params = tuple(base_vals)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()


def excluir(codigo, fase, linha):
    """
    Compatível com banco com/sem coluna de linha:
    - Se existir linha_col: usa no WHERE
    - Se não existir: ignora linha e remove por (codigo, fase)
    """
    linha_col = _resolve_linha_column()

    if linha_col:
        query = sql.SQL("DELETE FROM modelos WHERE codigo = %s AND fase = %s AND {} = %s").format(
            sql.Identifier(linha_col)
        )
        params = (codigo, fase, linha)
    else:
        query = sql.SQL("DELETE FROM modelos WHERE codigo = %s AND fase = %s")
        params = (codigo, fase)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
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
    Compatível com banco com/sem coluna de linha.
    Casts por campo:
    - meta_padrao: numeric
    - tempo_montagem: numeric (mantém decimais)
    - blank: int
    """
    linha_col = _resolve_linha_column()

    casts = {
        "meta_padrao": "::numeric",
        "tempo_montagem": "::numeric",
        "blank": "::int",
    }

    sets = ", ".join(f"{k} = %s{casts.get(k, '')}" for k in campos)
    valores = list(campos.values())

    if linha_col:
        query = sql.SQL(f"""
            UPDATE modelos
            SET {sets}
            WHERE codigo = %s AND fase = %s AND {linha_col} = %s
        """)
        valores.extend([codigo, fase, linha])
    else:
        query = sql.SQL(f"""
            UPDATE modelos
            SET {sets}
            WHERE codigo = %s AND fase = %s
        """)
        valores.extend([codigo, fase])

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, valores)
        conn.commit()
