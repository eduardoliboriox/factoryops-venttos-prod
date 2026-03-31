from __future__ import annotations

import math
import time
from typing import Optional

from app.repositories import time_studies_repository as repo


_DETAIL_CACHE_TTL_SECONDS = 5
_detail_cache: dict[int, tuple[float, dict]] = {}


def _cache_get(study_id: int) -> Optional[dict]:
    now = time.time()
    item = _detail_cache.get(int(study_id))
    if not item:
        return None
    expires_at, payload = item
    if now >= expires_at:
        _detail_cache.pop(int(study_id), None)
        return None
    return payload


def _cache_set(study_id: int, payload: dict):
    _detail_cache[int(study_id)] = (time.time() + _DETAIL_CACHE_TTL_SECONDS, payload)


def _cache_invalidate(study_id: Optional[int] = None):
    if study_id is None:
        _detail_cache.clear()
        return
    _detail_cache.pop(int(study_id), None)


def _dispatch_push(title: str, body: str, url: str = "/smt/estudo-tempo") -> None:
    try:
        from app.services.notification_service import notify_all
        notify_all(title=title, body=body, url=url)
    except Exception:
        pass


def _compute_uph_theoretical_no_loss(tempo_ciclo_sec: float) -> int:
    if not tempo_ciclo_sec or tempo_ciclo_sec <= 0:
        return 0
    uph = (3600.0 / float(tempo_ciclo_sec))
    return int(math.floor(uph))


def _compute_uph_real(tempo_ciclo_sec: float, perda_padrao: float) -> int:
    if not tempo_ciclo_sec or tempo_ciclo_sec <= 0:
        return 0

    perda = float(perda_padrao or 0.10)
    perda = min(max(perda, 0.0), 0.8)
    uph = (3600.0 / float(tempo_ciclo_sec)) * (1.0 - perda)
    return int(math.floor(uph))


def _compute_upd(uph_real: int, horas_turno: float) -> int:
    if not uph_real or uph_real <= 0:
        return 0
    horas = float(horas_turno or 8.30)
    horas = min(max(horas, 1.0), 24.0)
    return int(round(uph_real * horas))


def _compute_takt_time_sec(uph_meta: int) -> Optional[float]:
    if not uph_meta or uph_meta <= 0:
        return None
    return 3600.0 / float(uph_meta)


def _compute_cycle_target_with_loss_sec(uph_meta: int, perda_padrao: float) -> Optional[float]:
    if not uph_meta or uph_meta <= 0:
        return None
    perda = float(perda_padrao or 0.10)
    perda = min(max(perda, 0.0), 0.8)
    return (3600.0 * (1.0 - perda)) / float(uph_meta)


def _compute_upd_meta(uph_meta: int, horas_turno: float) -> int:
    if not uph_meta or uph_meta <= 0:
        return 0
    horas = float(horas_turno or 8.30)
    horas = min(max(horas, 1.0), 24.0)
    return int(round(float(uph_meta) * horas))


def _balance_status(uph_real: int, uph_meta: int) -> str:
    if not uph_meta or uph_meta <= 0:
        return "OK"
    return "OK" if uph_real >= uph_meta else "BALANCE"


def _recommendation_for_op(*, tempo_ciclo_sec: float, uph_meta: int, perda_padrao: float) -> Optional[dict]:
    if not tempo_ciclo_sec or tempo_ciclo_sec <= 0:
        return None

    target = _compute_cycle_target_with_loss_sec(uph_meta, perda_padrao)
    if target is None or target <= 0:
        return None

    tempo = float(tempo_ciclo_sec)
    if tempo <= target:
        return {
            "status": "OK",
            "cycle_target_sec": float(target),
            "delta_sec": 0.0,
            "delta_pct": 0.0,
            "parallel_factor": 1.0,
            "parallel_suggested": 1,
        }

    delta_sec = tempo - target
    delta_pct = (delta_sec / tempo) * 100.0 if tempo > 0 else 0.0
    parallel_factor = tempo / target
    parallel_suggested = int(math.ceil(parallel_factor))

    return {
        "status": "BALANCE",
        "cycle_target_sec": float(target),
        "delta_sec": float(delta_sec),
        "delta_pct": float(delta_pct),
        "parallel_factor": float(parallel_factor),
        "parallel_suggested": int(max(2, parallel_suggested)),
    }


def _hc_status(sum_hc: float, hc_meta: float) -> str:
    sum_hc = float(sum_hc or 0.0)
    hc_meta = float(hc_meta or 0.0)

    eps = 0.01
    if sum_hc > (hc_meta + eps):
        return "OVER"
    if sum_hc < (hc_meta - eps):
        return "UNDER"
    return "OK"


def list_studies(limit: int = 50):
    return repo.list_studies(limit=limit)


def create_study(data: dict, user=None):
    user_id = getattr(user, "id", None) if user else None
    username = getattr(user, "username", None) if user else None
    username = username or (getattr(user, "email", None) if user else None)

    produto = (data.get("produto") or "").strip()
    if not produto:
        raise ValueError("Produto é obrigatório")

    created = repo.create_study(data, user_id=user_id, username=username)
    _cache_invalidate(created.get("id"))

    actor = username or "Usuário"
    linha = (data.get("linha") or "").strip()
    _dispatch_push(
        title="Novo estudo de tempo criado",
        body=f"{actor} criou um estudo para {produto}" + (f" na linha {linha}." if linha else "."),
    )

    return created


def delete_study(study_id: int):
    repo.delete_study(study_id)
    _cache_invalidate(study_id)


def get_study_detail(study_id: int) -> Optional[dict]:
    cached = _cache_get(study_id)
    if cached is not None:
        return cached

    study = repo.get_study(study_id)
    if not study:
        return None

    ops = repo.list_operations(study_id)

    uph_meta = int(study.get("uph_meta") or 0)
    hc_meta = float(study.get("hc_meta") or 0)
    perda_padrao = float(study.get("perda_padrao") or 0.10)
    horas_turno = float(study.get("horas_turno") or 8.30)

    computed_ops = []
    line_uph_bottleneck = None
    line_uph_bottleneck_no_loss = None
    balance_count = 0
    sum_hc_ops = 0.0

    for op in ops:
        tempo = float(op.get("tempo_ciclo_sec") or 0)
        hc = float(op.get("hc") or 0)
        sum_hc_ops += hc

        uph_no_loss = _compute_uph_theoretical_no_loss(tempo)
        uph_real = _compute_uph_real(tempo, perda_padrao)
        upd = _compute_upd(uph_real, horas_turno)
        status = _balance_status(uph_real, uph_meta)

        if line_uph_bottleneck is None:
            line_uph_bottleneck = uph_real
        else:
            line_uph_bottleneck = min(line_uph_bottleneck, uph_real)

        if line_uph_bottleneck_no_loss is None:
            line_uph_bottleneck_no_loss = uph_no_loss
        else:
            line_uph_bottleneck_no_loss = min(line_uph_bottleneck_no_loss, uph_no_loss)

        if status == "BALANCE":
            balance_count += 1

        recommendation = _recommendation_for_op(
            tempo_ciclo_sec=tempo,
            uph_meta=uph_meta,
            perda_padrao=perda_padrao,
        )

        computed_ops.append({
            **op,
            "uph_theoretical": uph_no_loss,
            "uph_real": uph_real,
            "upd": upd,
            "balance": status,
            "recommendation": recommendation,
        })

    takt_time_sec = _compute_takt_time_sec(uph_meta)
    cycle_target_sec = _compute_cycle_target_with_loss_sec(uph_meta, perda_padrao)
    upd_meta = _compute_upd_meta(uph_meta, horas_turno)
    line_uph_bottleneck = int(line_uph_bottleneck or 0)
    line_uph_bottleneck_no_loss = int(line_uph_bottleneck_no_loss or 0)
    line_gap_uph = int(max((uph_meta - line_uph_bottleneck), 0)) if uph_meta > 0 else 0
    line_loss_gap_uph = int(max((line_uph_bottleneck_no_loss - line_uph_bottleneck), 0))
    sum_hc_ops = float(sum_hc_ops or 0.0)
    hc_status = _hc_status(sum_hc_ops, hc_meta)
    hc_gap = float(sum_hc_ops - hc_meta)

    totals = {
        "total_tempo_sec": float(sum(float(o.get("tempo_ciclo_sec") or 0) for o in ops)),
        "total_ops": len(ops),

        "uph_meta": uph_meta,
        "hc_meta": float(hc_meta),

        "takt_time_sec": float(takt_time_sec) if takt_time_sec is not None else None,
        "upd_meta": int(upd_meta),
        "cycle_target_sec": float(cycle_target_sec) if cycle_target_sec is not None else None,
        "perda_padrao": float(perda_padrao),

        "balance_count": int(balance_count),

        "line_uph_bottleneck": int(line_uph_bottleneck),
        "line_gap_uph": int(line_gap_uph),

        "line_uph_bottleneck_no_loss": int(line_uph_bottleneck_no_loss),
        "line_loss_gap_uph": int(line_loss_gap_uph),

        "sum_hc_ops": float(sum_hc_ops),
        "hc_gap": float(hc_gap),
        "hc_status": str(hc_status),
    }

    payload = {
        "study": study,
        "operations": computed_ops,
        "totals": totals,
    }

    _cache_set(study_id, payload)
    return payload


def add_operation(study_id: int, data: dict):
    operacao = (data.get("operacao") or "").strip()
    if not operacao:
        raise ValueError("Operação é obrigatória")

    tempo = float(data.get("tempo_ciclo_sec") or 0)
    if tempo <= 0:
        raise ValueError("Tempo de ciclo inválido")

    created = repo.add_operation(study_id, data)
    _cache_invalidate(study_id)
    return created


def update_operation(op_id: int, data: dict):
    updated = repo.update_operation(op_id, data)
    _cache_invalidate(None)
    return updated


def delete_operation(op_id: int):
    repo.delete_operation(op_id)
    _cache_invalidate(None)
