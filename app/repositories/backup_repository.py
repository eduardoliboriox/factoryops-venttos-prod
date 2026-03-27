from app.extensions import get_db
from psycopg.rows import dict_row


def get_backup_config():
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM backup_config ORDER BY id LIMIT 1")
            return cur.fetchone()


def upsert_backup_config(data: dict):
    existing = get_backup_config()

    with get_db() as conn:
        with conn.cursor() as cur:
            if existing:
                cur.execute("""
                    UPDATE backup_config
                    SET database_url     = %s,
                        frequency        = %s,
                        execution_hour   = %s,
                        execution_minute = %s,
                        retention_days   = %s,
                        is_active        = %s,
                        updated_at       = NOW()
                    WHERE id = %s
                """, (
                    data["database_url"],
                    data["frequency"],
                    data["execution_hour"],
                    data["execution_minute"],
                    data["retention_days"],
                    data["is_active"],
                    existing["id"],
                ))
            else:
                cur.execute("""
                    INSERT INTO backup_config
                        (database_url, frequency, execution_hour, execution_minute, retention_days, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    data["database_url"],
                    data["frequency"],
                    data["execution_hour"],
                    data["execution_minute"],
                    data["retention_days"],
                    data["is_active"],
                ))
            conn.commit()


def create_backup_log(data: dict):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO backup_logs
                    (status, file_path, size_bytes, duration_ms, checksum, error_message)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                data["status"],
                data.get("file_path"),
                data.get("size_bytes"),
                data.get("duration_ms"),
                data.get("checksum"),
                data.get("error_message"),
            ))
            conn.commit()
            return cur.fetchone()


def list_backup_logs(limit: int = 50):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT * FROM backup_logs
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
            return cur.fetchall()


def delete_old_logs(retention_days: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM backup_logs
                WHERE timestamp < NOW() - INTERVAL '%s days'
                  AND id NOT IN (
                      SELECT id FROM backup_logs
                      WHERE status = 'success'
                      ORDER BY timestamp DESC
                      LIMIT 1
                  )
            """, (retention_days,))
            conn.commit()
