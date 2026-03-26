from __future__ import annotations

import json
import logging

from flask import current_app
from pywebpush import webpush, WebPushException

from app.repositories import push_repository

logger = logging.getLogger(__name__)


def _send_to_subscriptions(subscriptions: list[dict], title: str, body: str, url: str) -> dict:
    vapid_private = current_app.config.get("VAPID_PRIVATE_KEY")
    vapid_claims_email = current_app.config.get("VAPID_CLAIMS_EMAIL", "mailto:admin@smt.local")

    if not vapid_private:
        logger.warning("VAPID_PRIVATE_KEY não configurada — push ignorado")
        return {"sent": 0, "failed": 0, "skipped": True}

    if not subscriptions:
        return {"sent": 0, "failed": 0, "skipped": False}

    payload = json.dumps({"title": title, "body": body, "url": url})
    sent = 0
    failed = 0
    to_remove: list[str] = []

    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub["endpoint"],
            "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=vapid_private,
                vapid_claims={"sub": vapid_claims_email},
            )
            sent += 1
        except WebPushException as exc:
            status = getattr(exc.response, "status_code", None) if exc.response else None
            if status in (404, 410):
                to_remove.append(sub["endpoint"])
            else:
                logger.error("Push falhou para endpoint %s: %s", sub["endpoint"][:40], exc)
            failed += 1
        except Exception as exc:
            logger.error("Erro inesperado no push: %s", exc)
            failed += 1

    for endpoint in to_remove:
        try:
            push_repository.delete_subscription(endpoint)
        except Exception as exc:
            logger.error("Falha ao remover subscription expirada: %s", exc)

    return {"sent": sent, "failed": failed, "skipped": False}


def notify_admins(title: str, body: str, url: str = "/admin/users") -> dict:
    from app.auth.repository import list_admin_user_ids
    admin_ids = list_admin_user_ids()
    subscriptions = push_repository.list_subscriptions_by_user_ids(admin_ids)
    return _send_to_subscriptions(subscriptions, title, body, url)


def notify_all(title: str, body: str, url: str = "/") -> dict:
    subscriptions = push_repository.list_all_subscriptions()
    return _send_to_subscriptions(subscriptions, title, body, url)
