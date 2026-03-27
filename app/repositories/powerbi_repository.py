from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Any


def _default_month_range(today: date | None = None) -> tuple[str, str]:
    hoje = today or date.today()
    primeiro = date(hoje.year, hoje.month, 1)
    ultimo = date(hoje.year, hoje.month, monthrange(hoje.year, hoje.month)[1])
    return primeiro.isoformat(), ultimo.isoformat()


def _normalize_filtros(raw: dict) -> dict:
    filtros = dict(raw or {})

    padrao_inicio, padrao_fim = _default_month_range()

    filtros["data_inicial"] = filtros.get("data_inicial") or padrao_inicio
    filtros["data_final"] = filtros.get("data_final") or padrao_fim

    filtros["turno"] = filtros.get("turno") or ""
    filtros["filial"] = filtros.get("filial") or ""
    filtros["setor"] = filtros.get("setor") or ""
    filtros["linha"] = filtros.get("linha") or ""

    return filtros


def resumo_powerbi_solicitacoes(filtros: dict) -> dict[str, Any]:
    filtros = _normalize_filtros(filtros)

    from app.services.solicitacoes_service import (
        ranking_extras_dashboard,
        ranking_solicitacoes_por_cliente,
        ranking_solicitacoes_por_tipo,
        resumo_solicitacoes_dashboard,
        kpis_dashboard_abs_linhas,
    )

    sol = resumo_solicitacoes_dashboard(filtros)
    extras = ranking_extras_dashboard(filtros)
    abs_linhas = kpis_dashboard_abs_linhas(filtros)

    clientes = ranking_solicitacoes_por_cliente(filtros)
    tipos = ranking_solicitacoes_por_tipo(filtros)

    extras_provisionado = round(
        sum(float(x.get("provisionado") or 0) for x in (extras or [])),
        2,
    )
    extras_realizado = round(
        sum(float(x.get("realizado") or 0) for x in (extras or [])),
        2,
    )

    kpis = {
        "solicitacoes_abertas": int(sol.get("abertas") or 0),
        "solicitacoes_realizadas": int(sol.get("fechadas") or 0),
        "total_gasto": float(sol.get("total_gasto") or 0.0),
        "extras_provisionado": float(extras_provisionado),
        "extras_realizado": float(extras_realizado),
        "absenteismo": float(abs_linhas.get("absenteismo") or 0.0),
        "linhas": int(abs_linhas.get("linhas") or 0),
    }

    return {
        "filtros": filtros,
        "kpis": kpis,
        "rankings": {
            "clientes": clientes or [],
            "extras": extras or [],
            "tipos": tipos or [],
        },
    }
