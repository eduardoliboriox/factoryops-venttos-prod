from datetime import date
from app.repositories import producao_coletada_repository as repo
from app.repositories import linha_config_repository as lc_repo

_TURNOS_VALIDOS = {"1º Turno", "2º Turno", "3º Turno"}


def data_padrao() -> tuple[str, str]:
    hoje = str(date.today())
    return hoje, hoje


def listar(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "") -> list:
    registros = repo.listar(data_inicial, data_final, setor, linha, turno)
    return [r for r in registros if r.get("origem") == "manual"]


def filtros_disponiveis() -> dict:
    por_setor = lc_repo.listar_por_setor()
    return {
        "setores":       sorted(por_setor.keys()),
        "linhas_por_setor": {s: [r["linha"] for r in linhas] for s, linhas in por_setor.items()},
    }


def inserir(form_data: dict) -> None:
    data    = form_data.get("data", "").strip()
    setor   = form_data.get("setor", "").strip()
    linha   = form_data.get("linha", "").strip()
    turno   = form_data.get("turno", "").strip()
    modelo  = form_data.get("modelo", "").strip()

    if not data:
        raise ValueError("Data é obrigatória.")
    if not setor:
        raise ValueError("Setor é obrigatório.")
    if not linha:
        raise ValueError("Linha é obrigatória.")
    if turno not in _TURNOS_VALIDOS:
        raise ValueError(f"Turno inválido: {turno}.")
    if not modelo:
        raise ValueError("Modelo é obrigatório.")

    try:
        producao_real = int(form_data.get("producao_real", "0"))
    except (ValueError, TypeError):
        raise ValueError("Produção deve ser um número inteiro.")

    if producao_real <= 0:
        raise ValueError("Produção deve ser maior que zero.")

    try:
        qtd_perda = int(form_data.get("qtd_perda", "0") or "0")
        defeitos  = int(form_data.get("defeitos",  "0") or "0")
    except (ValueError, TypeError):
        raise ValueError("Perda e defeitos devem ser números inteiros.")

    repo.inserir_manual({
        "data":          data,
        "setor":         setor,
        "linha":         linha,
        "turno":         turno,
        "modelo":        modelo,
        "producao_real": producao_real,
        "qtd_perda":     qtd_perda,
        "defeitos":      defeitos,
        "observacao":    form_data.get("observacao", "").strip() or None,
    })


def excluir(registro_id: int) -> None:
    if not registro_id or registro_id >= 0:
        raise ValueError("Registro inválido.")
    repo.excluir_manual(registro_id)
