from __future__ import annotations

from typing import Optional, Any

from psycopg.rows import dict_row
from psycopg import sql
from psycopg.types.json import Json

from app.extensions import get_db


_LINHA_COL_CACHE: Optional[str] = None
_LINHA_COL_CHECKED: bool = False

_AUDIT_READY: bool = False


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


def _ensure_audit_schema():
    """
    Cria tabela/índices de auditoria de forma idempotente.
    Não depende de Alembic. Seguro para prod e dev.
    """
    global _AUDIT_READY
    if _AUDIT_READY:
        return

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS modelos_audit (
                    id BIGSERIAL PRIMARY KEY,
                    codigo TEXT NOT NULL,
                    fase TEXT NOT NULL,
                    linha TEXT,
                    action TEXT NOT NULL, -- CREATE / UPDATE / DELETE
                    changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    changed_by_user_id BIGINT,
                    changed_by_username TEXT,
                    changes JSONB
                )
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_modelos_audit_lookup
                ON modelos_audit (codigo, fase, linha, changed_at DESC)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_modelos_audit_changed_at
                ON modelos_audit (changed_at DESC)
            """)

        conn.commit()

    _AUDIT_READY = True


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


def _select_modelo_row(cur, codigo: str, fase: str, linha: Optional[str]) -> Optional[dict]:
    """
    Busca o registro atual do modelo para auditoria.
    Compatível com banco com/sem coluna linha.
    """
    linha_col = _resolve_linha_column()

    if linha_col:
        q = sql.SQL("""
            SELECT
              codigo, cliente, setor, {linha_col} AS linha,
              meta_padrao, tempo_montagem, blank, fase
            FROM modelos
            WHERE codigo = %s AND fase = %s AND {linha_col} = %s
            LIMIT 1
        """).format(linha_col=sql.Identifier(linha_col))
        cur.execute(q, (codigo, fase, linha))
        return cur.fetchone()

    q = """
        SELECT codigo, cliente, setor, NULL::text AS linha,
               meta_padrao, tempo_montagem, blank, fase
        FROM modelos
        WHERE codigo = %s AND fase = %s
        LIMIT 1
    """
    cur.execute(q, (codigo, fase))
    return cur.fetchone()


def _audit_insert(cur, *, codigo: str, fase: str, linha: Optional[str],
                  action: str, user_id: Optional[int], username: Optional[str],
                  changes: Optional[dict]):
    _ensure_audit_schema()

    cur.execute(
        """
        INSERT INTO modelos_audit
            (codigo, fase, linha, action, changed_by_user_id, changed_by_username, changes)
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (codigo, fase, linha, action, user_id, username, Json(changes) if changes is not None else None)
    )


def buscar_meta_padrao(codigo: str, fase: str, linha: Optional[str]) -> Optional[float]:
    linha_col = _resolve_linha_column()

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if linha_col:
                q = sql.SQL("""
                    SELECT meta_padrao FROM modelos
                    WHERE codigo = %s AND fase = %s AND {} = %s
                    LIMIT 1
                """).format(sql.Identifier(linha_col))
                cur.execute(q, (codigo, fase, linha))
            else:
                cur.execute(
                    "SELECT meta_padrao FROM modelos WHERE codigo = %s AND fase = %s LIMIT 1",
                    (codigo, fase)
                )
            row = cur.fetchone()
            return float(row["meta_padrao"]) if row and row["meta_padrao"] is not None else None


def inserir(dados, *, audit_user_id: Optional[int] = None, audit_username: Optional[str] = None):
    """
    Compatível com banco com/sem coluna de linha.

    Importante:
    - tempo_montagem precisa manter 2 casas (DB deve ser NUMERIC(10,2))
    - meta_padrao idem (numeric)
    - blank é int
    """
    linha_col = _resolve_linha_column()

    if linha_col:
        cols = ["codigo", "cliente", "setor", linha_col, "meta_padrao", "tempo_montagem", "blank", "fase"]
        vals = [
            dados["codigo"],
            dados["cliente"],
            dados["setor"],
            (dados.get("linha") or "").strip() or None,
            dados["meta_padrao"],
            dados.get("tempo_montagem"),
            dados["blank"],
            dados["fase"],
        ]

        query = sql.SQL("""
            INSERT INTO modelos ({cols})
            VALUES (
                %s, %s, %s, NULLIF(%s, '')::text,
                NULLIF(%s, '')::numeric,
                NULLIF(%s, '')::numeric,
                NULLIF(%s, '')::int,
                %s
            )
        """).format(cols=sql.SQL(", ").join(sql.Identifier(c) for c in cols))

        params = tuple(vals)

    else:
        cols = [
            "codigo",
            "cliente",
            "setor",
            "meta_padrao",
            "tempo_montagem",
            "blank",
            "fase",
        ]
        vals = [
            dados["codigo"],
            dados["cliente"],
            dados["setor"],
            dados["meta_padrao"],
            dados.get("tempo_montagem"),
            dados["blank"],
            dados["fase"],
        ]

        query = sql.SQL("""
            INSERT INTO modelos ({cols})
            VALUES (
                %s, %s, %s,
                NULLIF(%s, '')::numeric,
                NULLIF(%s, '')::numeric,
                NULLIF(%s, '')::int,
                %s
            )
        """).format(cols=sql.SQL(", ").join(sql.Identifier(c) for c in cols))

        params = tuple(vals)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)

            codigo = str(dados.get("codigo") or "").strip()
            fase = str(dados.get("fase") or "").strip()
            linha = (dados.get("linha") or "").strip() or None

            if codigo and fase:
                _audit_insert(
                    cur,
                    codigo=codigo,
                    fase=fase,
                    linha=linha,
                    action="CREATE",
                    user_id=audit_user_id,
                    username=audit_username,
                    changes={"created": True}
                )

        conn.commit()


def excluir(codigo, fase, linha, *, audit_user_id: Optional[int] = None, audit_username: Optional[str] = None):
    """
    Compatível com banco com/sem coluna de linha:
    - Se existir linha_col: usa no WHERE
    - Se não existir: ignora linha e remove por (codigo, fase)

    Também registra auditoria (DELETE) com snapshot do que existia.
    """
    linha_col = _resolve_linha_column()

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            before = _select_modelo_row(cur, codigo, fase, linha)

            if linha_col:
                query = sql.SQL("DELETE FROM modelos WHERE codigo = %s AND fase = %s AND {} = %s").format(
                    sql.Identifier(linha_col)
                )
                params = (codigo, fase, linha)
            else:
                query = sql.SQL("DELETE FROM modelos WHERE codigo = %s AND fase = %s")
                params = (codigo, fase)

            cur.execute(query, params)

            if before:
                _audit_insert(
                    cur,
                    codigo=codigo,
                    fase=fase,
                    linha=(before.get("linha") or linha or None),
                    action="DELETE",
                    user_id=audit_user_id,
                    username=audit_username,
                    changes={"before": before, "deleted": True}
                )

        conn.commit()


def atualizar(codigo, fase, linha, campos, *, audit_user_id: Optional[int] = None, audit_username: Optional[str] = None):
    """
    Compatível com banco com/sem coluna de linha.
    Casts por campo:
    - meta_padrao: numeric
    - tempo_montagem: numeric (mantém decimais)
    - blank: int

    Auditoria (UPDATE):
    - salva before/after apenas dos campos alterados
    - salva também chave do modelo (codigo/fase/linha)
    """
    linha_col = _resolve_linha_column()

    casts = {
        "meta_padrao": sql.SQL("::numeric"),
        "tempo_montagem": sql.SQL("::numeric"),
        "blank": sql.SQL("::int"),
    }

    set_parts = []
    values: list[Any] = []

    for k, v in campos.items():
        cast = casts.get(k)
        if cast is not None:
            set_parts.append(sql.SQL("{} = %s").format(sql.Identifier(k)) + cast)
        else:
            set_parts.append(sql.SQL("{} = %s").format(sql.Identifier(k)))
        values.append(v)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            before = _select_modelo_row(cur, codigo, fase, linha)

            if linha_col:
                where_sql = sql.SQL("WHERE codigo = %s AND fase = %s AND {} = %s").format(sql.Identifier(linha_col))
                values_where = [codigo, fase, linha]
            else:
                where_sql = sql.SQL("WHERE codigo = %s AND fase = %s")
                values_where = [codigo, fase]

            q = sql.SQL("UPDATE modelos SET ") + sql.SQL(", ").join(set_parts) + sql.SQL(" ") + where_sql
            cur.execute(q, values + values_where)

            new_codigo = str(campos.get("codigo") or codigo).strip()
            after = _select_modelo_row(cur, new_codigo, fase, linha)

            if before:
                changes = {}
                for key in campos.keys():
                    changes[key] = {
                        "before": before.get(key),
                        "after": (after.get(key) if after else None),
                    }

                _audit_insert(
                    cur,
                    codigo=new_codigo,
                    fase=fase,
                    linha=(after.get("linha") if after else (before.get("linha") or linha or None)),
                    action="UPDATE",
                    user_id=audit_user_id,
                    username=audit_username,
                    changes={
                        "changed_fields": list(campos.keys()),
                        "diff": changes
                    }
                )

        conn.commit()


def listar_historico(codigo: str, fase: str, linha: Optional[str], limit: int = 50):
    """
    Retorna histórico do modelo (filtra corretamente por codigo + fase + linha).
    """
    _ensure_audit_schema()

    codigo = (codigo or "").strip()
    fase = (fase or "").strip()
    linha = (linha or "").strip() or None

    if not codigo or not fase:
        return []

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                  id,
                  action,
                  changed_at,
                  changed_by_username,
                  changed_by_user_id,
                  changes
                FROM modelos_audit
                WHERE codigo = %s
                  AND fase = %s
                  AND (linha IS NOT DISTINCT FROM %s)
                ORDER BY changed_at DESC
                LIMIT %s
                """,
                (codigo, fase, linha, limit)
            )
            return cur.fetchall() or []
