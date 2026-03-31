import click
from app.extensions import get_db


@click.command("generate-employee-codes")
@click.option("--start", default=1010, help="Initial numeric code (default 1010 -> 001010)")
def generate_employee_codes(start: int):
    """
    Generate sequential employee codes for employees that don't have one.

    Example:
        flask generate-employee-codes
        flask generate-employee-codes --start 2000
    """

    print(f"🚀 Generating employee codes starting at {start:06}")

    with get_db() as conn:
        with conn.cursor() as cur:

            # pega somente quem ainda NÃO tem código
            cur.execute("""
                SELECT id
                FROM employees
                WHERE employee_code IS NULL
                ORDER BY id
            """)

            rows = cur.fetchall()

            if not rows:
                print("✅ All employees already have codes.")
                return

            code = start

            updates = [
                (f"{code + i:06}", r["id"])
                for i, r in enumerate(rows)
            ]

            cur.executemany("""
                UPDATE employees
                SET employee_code = %s
                WHERE id = %s
            """, updates)

        conn.commit()

    print(f"✅ {len(updates)} codes generated successfully!")
