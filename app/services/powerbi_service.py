from __future__ import annotations

from typing import Any


def resumo_powerbi_solicitacoes(filtros: dict) -> dict[str, Any]:

    from app.repositories.powerbi_repository import (
        resumo_powerbi_solicitacoes as repo_resumo_powerbi_solicitacoes,
    )

    return repo_resumo_powerbi_solicitacoes(filtros)
