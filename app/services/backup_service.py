import os
import hashlib
import subprocess
import time
import threading
from datetime import datetime
from flask import current_app


_backup_thread = None
_scheduler_lock = threading.Lock()


def _compute_checksum(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_pg_dump(database_url: str, output_path: str) -> dict:
    start = time.monotonic()
    result = {"status": "failure", "file_path": None, "size_bytes": None,
              "duration_ms": None, "checksum": None, "error_message": None}

    try:
        proc = subprocess.run(
            ["pg_dump", "--no-password", database_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=600,
        )

        if proc.returncode != 0:
            result["error_message"] = proc.stderr.decode("utf-8", errors="replace")[:2000]
            return result

        import gzip
        with open(output_path + ".gz", "wb") as gz_out:
            gz_out.write(gzip.compress(proc.stdout))

        final_path = output_path + ".gz"
        result["status"] = "success"
        result["file_path"] = final_path
        result["size_bytes"] = os.path.getsize(final_path)
        result["checksum"] = _compute_checksum(final_path)

    except subprocess.TimeoutExpired:
        result["error_message"] = "pg_dump timeout (600s)"
    except FileNotFoundError:
        result["error_message"] = "pg_dump não encontrado no PATH do sistema"
    except Exception as e:
        result["error_message"] = str(e)[:2000]
    finally:
        elapsed = time.monotonic() - start
        result["duration_ms"] = int(elapsed * 1000)
        if os.path.exists(output_path):
            os.remove(output_path)

    return result


def _get_backup_dir(frequency: str) -> str:
    base = os.path.join(os.getcwd(), "backups", frequency)
    os.makedirs(base, exist_ok=True)
    return base


def execute_backup(app=None):
    ctx = app.app_context() if app else current_app._get_current_object().app_context()

    with ctx:
        from app.repositories.backup_repository import (
            get_backup_config,
            create_backup_log,
            delete_old_logs,
        )

        config = get_backup_config()
        if not config or not config.get("database_url"):
            return

        frequency = config.get("frequency", "daily")
        retention_days = config.get("retention_days", 30)
        database_url = config["database_url"]

        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
        backup_dir = _get_backup_dir(frequency)
        output_path = os.path.join(backup_dir, f"backup_{timestamp}.sql")

        result = _run_pg_dump(database_url, output_path)
        create_backup_log(result)

        if result["status"] == "success":
            delete_old_logs(retention_days)


def trigger_manual_backup():
    app = current_app._get_current_object()
    t = threading.Thread(target=execute_backup, args=(app,), daemon=True)
    t.start()


def _scheduler_loop(app, config: dict):
    import time as _time
    from app.repositories.backup_repository import get_backup_config

    while True:
        try:
            with app.app_context():
                cfg = get_backup_config()

            if not cfg or not cfg.get("is_active"):
                _time.sleep(60)
                continue

            now = datetime.utcnow()
            target_h = cfg.get("execution_hour", 2)
            target_m = cfg.get("execution_minute", 0)

            if now.hour == target_h and now.minute == target_m:
                execute_backup(app)
                _time.sleep(61)
            else:
                _time.sleep(30)
        except Exception:
            _time.sleep(60)


def start_backup_scheduler(app):
    global _backup_thread

    with _scheduler_lock:
        if _backup_thread is not None and _backup_thread.is_alive():
            return

        config = {}
        _backup_thread = threading.Thread(
            target=_scheduler_loop,
            args=(app, config),
            daemon=True,
            name="backup-scheduler",
        )
        _backup_thread.start()
