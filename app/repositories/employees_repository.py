from app.extensions import get_db
from psycopg.rows import dict_row

def get_employee_by_matricula(matricula: str):

    matricula = matricula.strip()

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:

            cur.execute("""
                SELECT
                    e.full_name,
                    p.phone,
                    CONCAT_WS(', ',
                        p.street,
                        p.number,
                        p.neighborhood,
                        p.city,
                        p.state
                    ) AS endereco
                FROM employees e
                LEFT JOIN users u
                  ON (
                       u.employee_id = e.id
                       OR ltrim(u.matricula, '0') = ltrim(e.employee_code, '0')
                     )
                LEFT JOIN user_profiles p
                  ON p.user_id = u.id
                WHERE ltrim(e.employee_code, '0') = ltrim(%s, '0')
                LIMIT 1
            """, (matricula,))

            employee = cur.fetchone()

            if employee:
                return employee

            cur.execute("""
                SELECT
                    u.full_name,
                    p.phone,
                    CONCAT_WS(', ',
                        p.street,
                        p.number,
                        p.neighborhood,
                        p.city,
                        p.state
                    ) AS endereco
                FROM users u
                LEFT JOIN user_profiles p
                  ON p.user_id = u.id
                WHERE u.matricula = %s
                LIMIT 1
            """, (matricula,))

            return cur.fetchone()

def get_clt_remuneracao_mensal_by_matricula(matricula: str):
    """
    Retorna remuneracao_mensal (NUMERIC) do CLT, se existir.
    - usa users.user_type = 'CLT'
    - busca via users.matricula (normalizando zeros)
    """
    matricula = (matricula or "").strip()

    if not matricula:
        return None

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    up.remuneracao_mensal
                FROM users u
                JOIN user_profiles up
                  ON up.user_id = u.id
                WHERE u.user_type = 'CLT'
                  AND ltrim(u.matricula, '0') = ltrim(%s, '0')
                LIMIT 1
            """, (matricula,))
            row = cur.fetchone()
            if not row:
                return None
            return row.get("remuneracao_mensal")
