from __future__ import annotations

import time

from app.repositories import production_lines_repository as repo


_CACHE_TTL_SECONDS = 60

_cache_sectors_value = None
_cache_sectors_expires = 0.0

_cache_lines_by_sector: dict[str, tuple[list[str], float]] = {}


def _now() -> float:
    return time.time()


def list_sectors() -> list[str]:
    global _cache_sectors_value, _cache_sectors_expires

    now = _now()
    if _cache_sectors_value is not None and now < _cache_sectors_expires:
        return _cache_sectors_value

    data = repo.list_sectors()
    _cache_sectors_value = data
    _cache_sectors_expires = now + _CACHE_TTL_SECONDS
    return data


def list_lines_by_sector(setor: str) -> list[str]:
    setor = (setor or "").strip()
    if not setor:
        return []

    now = _now()
    cached = _cache_lines_by_sector.get(setor)
    if cached and now < cached[1]:
        return cached[0]

    data = repo.list_lines_by_sector(setor)
    _cache_lines_by_sector[setor] = (data, now + _CACHE_TTL_SECONDS)
    return data
