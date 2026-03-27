import click
import pandas as pd
from pathlib import Path
from flask import current_app

from app.extensions import get_db


def normalize_status(value: str) -> str:
    if pd.isna(value):
        return "INACTIVE"

    v = str(value).strip().lower()
    return "ACTIVE" if "ativo" in v else "INACTIVE"


@click.command("import-employees")
def import_employees():
    """
    Import employees from official spreadsheet.
    Column A (Chapa) is used as employee_code.
    """

    project_root = Path(current_app.root_path).parent
    data_dir = project_root / "data"

    excel_file = next(data_dir.glob("Lista-de-Funcionarios-Venttos-17-12-25-Completo.*"))
    engine = "xlrd" if excel_file.suffix.lower() == ".xls" else "openpyxl"

    df = pd.read_excel(excel_file, engine=engine)

    # Map columns explicitly
    df = df.rename(columns={
        df.columns[0]: "employee_code",   # CHAPA
        df.columns[1]: "full_name",
        df.columns[2]: "job_title",
        df.columns[3]: "department",
        df.columns[4]: "hired_at",
        df.columns[5]: "status",
        df.columns[6]: "branch_name",
    })

    df["employee_code"] = df["employee_code"].astype(str).str.strip()
    df["status"] = df["status"].apply(normalize_status)
    df["hired_at"] = pd.to_datetime(df["hired_at"], errors="coerce").dt.date

    rows = [
        (
            r.employee_code,
            r.full_name.strip(),
            r.job_title,
            r.department,
            r.hired_at,
            r.status,
            r.branch_name
        )
        for r in df.itertuples(index=False)
        if r.employee_code and r.full_name
    ]

    with get_db() as conn:
        with conn.cursor() as cur:

            # Reset total (ambiente inicial)
            cur.execute("TRUNCATE TABLE employees RESTART IDENTITY CASCADE;")

            cur.executemany("""
                INSERT INTO employees (
                    employee_code,
                    full_name,
                    job_title,
                    department,
                    hired_at,
                    status,
                    branch_name
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, rows)

        conn.commit()

    print(f"✅ {len(rows)} employees imported with REAL employee_code (chapa).")
