import os
from pathlib import Path
import pandas as pd
import psycopg

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

BASE_DIR = Path(__file__).resolve().parents[2]

EXCEL_PATH = None
for ext in ["xls", "xlsx", "XLS", "XLSX"]:
    candidate = BASE_DIR / "app" / "data" / f"Lista-de-Funcionarios-Venttos-17-12-25-Completo.{ext}"
    if candidate.exists():
        EXCEL_PATH = candidate
        break

if not EXCEL_PATH:
    raise FileNotFoundError(
        "Excel not found in app/data: Lista-de-Funcionarios-Venttos-17-12-25-Completo.[xls,xlsx]"
    )

engine = "xlrd" if EXCEL_PATH.suffix.lower() == ".xls" else "openpyxl"

def normalize_status(value) -> str:
    if pd.isna(value):
        return "INACTIVE"
    v = str(value).strip().lower()
    return "ACTIVE" if "ativo" in v else "INACTIVE"

def main():
    print(f"📊 Reading Excel: {EXCEL_PATH.name} ...")

    df = pd.read_excel(EXCEL_PATH, engine=engine)

    df = df.rename(columns={
        df.columns[1]: "full_name",    # Coluna B
        df.columns[2]: "job_title",    # Coluna C
        df.columns[3]: "department",   # Coluna D
        df.columns[4]: "hired_at",     # Coluna E
        df.columns[5]: "status",       # Coluna F
        df.columns[6]: "branch_name",  # Coluna G
    })

    df = df[["full_name", "job_title", "department", "hired_at", "status", "branch_name"]]

    df["status"] = df["status"].apply(normalize_status)
    df["hired_at"] = pd.to_datetime(df["hired_at"], errors="coerce").dt.date

    rows = [
        (
            str(r.full_name).strip(),
            r.job_title,
            r.department,
            r.hired_at,
            r.status,
            r.branch_name
        )
        for r in df.itertuples(index=False)
        if r.full_name and str(r.full_name).strip()
    ]

    print(f"📌 Total rows after filtering: {len(rows)}")
    print(f"🚀 Importing employees into PostgreSQL...")

    with psycopg.connect(DATABASE_URL, sslmode="require", connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE employees RESTART IDENTITY;")
            cur.executemany("""
                INSERT INTO employees (
                    full_name,
                    job_title,
                    department,
                    hired_at,
                    status,
                    branch_name
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, rows)
        conn.commit()

    print("✅ Employees imported successfully!")

if __name__ == "__main__":
    main()
