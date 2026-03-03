from __future__ import annotations

import math
from typing import Optional

from app.repositories import time_studies_repository as repo


def _compute_uph_real(tempo_ciclo_sec: float, perda_padrao: float) -> int:
    """
    Baseado no Excel da engenharia:
    UPH Real ≈ (3600 / TempoCiclo) * (1 - perda_padrao)

    Ex:
    46.2s -> 3600/46.2=77.9 ; perda 10% -> 70.1 -> 70
    """
    if not tempo_ciclo_sec or tempo_ciclo_sec <= 0:
        return 0

    perda = float(perda_padrao or 0.10)
    perda = min(max(perda, 0.0), 0.8)  # trava de segurança (0%..80%)
    uph = (3600.0 / float(tempo_ciclo_sec)) * (1.0 - perda)
    return int(math.floor(uph))


def _compute_upd(uph_real: int, horas_turno: float) -> int:
    if not uph_real or uph_real <= 0:
        return 0

    horas = float(horas_turno or 8.30)
    horas = min(max(horas, 1.0), 24.0)
    return int(round(uph_real * horas))


def _compute_takt_time_sec(uph_meta: int) -> Optional[float]:
    """
    Takt Time (s/unidade) para bater a meta por hora:
    takt = 3600 / UPH_META
    Ex: UPH_META=70 => 51.43 s por peça
    """
    if not uph_meta or uph_meta <= 0:
        return None
    return 3600.0 / float(uph_meta)


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


def list_studies(limit: int = 50):
    return repo.list_studies(limit=limit)


def create_study(data: dict, user=None):
    user_id = getattr(user, "id", None) if user else None
    username = getattr(user, "username", None) if user else None
    username = username or (getattr(user, "email", None) if user else None)

    produto = (data.get("produto") or "").strip()
    if not produto:
        raise ValueError("Produto é obrigatório")

    return repo.create_study(data, user_id=user_id, username=username)


def delete_study(study_id: int):
    repo.delete_study(study_id)


def get_study_detail(study_id: int) -> Optional[dict]:
    study = repo.get_study(study_id)
    if not study:
        return None

    ops = repo.list_operations(study_id)

    uph_meta = int(study.get("uph_meta") or 0)
    perda_padrao = float(study.get("perda_padrao") or 0.10)
    horas_turno = float(study.get("horas_turno") or 8.30)

    computed_ops = []
    for op in ops:
        tempo = float(op.get("tempo_ciclo_sec") or 0)
        uph_real = _compute_uph_real(tempo, perda_padrao)
        upd = _compute_upd(uph_real, horas_turno)
        status = _balance_status(uph_real, uph_meta)

        computed_ops.append({
            **op,
            "uph_real": uph_real,
            "upd": upd,
            "balance": status,
        })

    takt_time_sec = _compute_takt_time_sec(uph_meta)
    upd_meta = _compute_upd_meta(uph_meta, horas_turno)

    totals = {
        "total_tempo_sec": float(sum(float(o.get("tempo_ciclo_sec") or 0) for o in ops)),
        "total_ops": len(ops),
        "uph_meta": uph_meta,
        "hc_meta": float(study.get("hc_meta") or 0),

        # NOVO (para UI/entendimento)
        "takt_time_sec": float(takt_time_sec) if takt_time_sec is not None else None,
        "upd_meta": int(upd_meta),
    }

    return {
        "study": study,
        "operations": computed_ops,
        "totals": totals,
    }


def add_operation(study_id: int, data: dict):
    operacao = (data.get("operacao") or "").strip()
    if not operacao:
        raise ValueError("Operação é obrigatória")

    tempo = float(data.get("tempo_ciclo_sec") or 0)
    if tempo <= 0:
        raise ValueError("Tempo de ciclo inválido")

    return repo.add_operation(study_id, data)


def update_operation(op_id: int, data: dict):
    return repo.update_operation(op_id, data)


def delete_operation(op_id: int):
    repo.delete_operation(op_id)
