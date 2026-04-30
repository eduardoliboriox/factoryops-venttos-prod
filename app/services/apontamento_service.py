from datetime import date, time
from app.repositories import apontamento_repository as repo
from app.repositories import turno_config_repository as tc_repo
from app.repositories import controle_ops_repository as ops_repo
from app.repositories import roteiro_repository as roteiro_repo

SETORES_SMD = {"SMD"}

_TURNOS_NOTURNOS_FALLBACK: dict[str, tuple[time, time]] = {
    "2º Turno": (time(16, 48), time(2, 35)),
}


def data_padrao() -> tuple[str, str]:
    hoje = str(date.today())
    return hoje, hoje


def _hora_params_turno_noturno(turno: str) -> tuple:
    if not turno:
        return None, None
    for c in tc_repo.listar():
        if c["turno"] == turno and c["hora_fim"] < c["hora_inicio"]:
            return c["hora_inicio"], c["hora_fim"]
    if turno in _TURNOS_NOTURNOS_FALLBACK:
        return _TURNOS_NOTURNOS_FALLBACK[turno]
    return None, None


def listar_agrupado(data_inicial: str, data_final: str, setor: str = "", linha: str = "", turno: str = "", sistema: str = "") -> list:
    hora_ini, hora_fim = _hora_params_turno_noturno(turno)
    return repo.listar_agrupado(data_inicial, data_final, setor, linha, turno,
                                hora_inicio_turno=hora_ini, hora_fim_turno=hora_fim, sistema=sistema)


_ORDEM_SETORES = ["PTH", "SMD", "IM", "PA", "VTT"]


def ops_abertas(setor: str = "") -> list:
    return repo.ops_abertas(setor)


def _validar_setor_roteiro(modelo: str, setor: str) -> None:
    setores_validos = roteiro_repo.setores_do_modelo(modelo)
    if not setores_validos:
        return
    if setor not in setores_validos:
        raise ValueError(
            f"Setor '{setor}' não faz parte do roteiro do modelo '{modelo}'. "
            f"Setores válidos: {', '.join(setores_validos)}."
        )


def _validar_sequencia_roteiro(op: dict) -> None:
    numero_op = op.get("numero_op", "") or ""
    if len(numero_op) < 3:
        return
    base = numero_op[:-2]
    setor_atual = op.get("setor") or ""

    modelo = (op.get("produto") or "").strip().upper()
    setores_roteiro = roteiro_repo.setores_do_modelo(modelo) if modelo else []
    ordem_setores = setores_roteiro if setores_roteiro else _ORDEM_SETORES

    try:
        idx_atual = ordem_setores.index(setor_atual)
    except ValueError:
        return

    familia = ops_repo.buscar_familia_op(base)
    for anterior in familia:
        if anterior["numero_op"] == numero_op:
            continue
        setor_ant = anterior["setor"] or ""
        try:
            idx_ant = ordem_setores.index(setor_ant)
        except ValueError:
            continue
        if idx_ant < idx_atual and anterior["produzido"] == 0:
            raise ValueError(
                f"{setor_ant} (OP {anterior['numero_op']}) ainda não tem produção apontada. "
                "Siga o roteiro de produção."
            )


def vincular(data: str, turno: str, modelo: str, linha: str, op_id: int, quantidade: int,
             setor: str = "", fase: str = None, lote: str = None) -> None:
    if not data or not turno or not modelo or not linha:
        raise ValueError("Dados do apontamento incompletos.")
    if not op_id or op_id <= 0:
        raise ValueError("OP inválida.")
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")

    fase_norm = fase.strip().upper() if fase and fase.strip() else None

    if setor in SETORES_SMD and fase_norm not in ("TOP", "BOTTOM"):
        raise ValueError("Para SMD informe a fase: TOP ou BOTTOM.")
    if setor not in SETORES_SMD:
        fase_norm = None

    _validar_setor_roteiro(modelo, setor)

    op = repo.buscar_op_para_vincular(op_id)
    if not op:
        raise ValueError("OP não encontrada.")

    _validar_sequencia_roteiro(op)

    if op["produto"].strip().upper() != modelo.strip().upper():
        raise ValueError(
            f"Modelo incompatível: produção é '{modelo}' mas a OP é para '{op['produto']}'. "
            "Selecione a OP correta."
        )

    if op["fase_modelo"] == "AMBAS" and fase_norm:
        fase_feita = op["top_feito"] if fase_norm == "TOP" else op["bottom_feito"]
        disponivel = op["quantidade"] - fase_feita
        if quantidade > disponivel:
            raise ValueError(
                f"Saldo insuficiente para fase {fase_norm}: "
                f"disponível {disponivel}, solicitado {quantidade}."
            )
    else:
        if quantidade > op["saldo"]:
            raise ValueError(
                f"Saldo insuficiente: disponível {op['saldo']}, solicitado {quantidade}."
            )

    repo.vincular(data, turno, modelo, linha, op_id, quantidade, fase_norm, lote or None)


def desvincular(apontamento_id: int) -> None:
    if not apontamento_id or apontamento_id <= 0:
        raise ValueError("Apontamento inválido.")
    repo.desvincular(apontamento_id)


def corrigir_modelo(data: str, turno: str, setor: str, linha: str, modelo_atual: str, modelo_novo: str) -> None:
    modelo_novo = (modelo_novo or "").strip().upper()
    if not modelo_novo:
        raise ValueError("O novo código do modelo é obrigatório.")
    if modelo_novo == (modelo_atual or "").strip().upper():
        raise ValueError("O modelo novo é idêntico ao atual.")
    if not data or not turno or not setor or not linha or not modelo_atual:
        raise ValueError("Dados insuficientes para identificar o registro.")
    repo.corrigir_modelo(data, turno, setor, linha, modelo_atual, modelo_novo)


def fila_producao() -> dict:
    rows = repo.fila_producao()
    agrupado: dict = {}
    for row in rows:
        setor = row["setor"] or "Sem setor"
        agrupado.setdefault(setor, []).append(dict(row))
    resultado: dict = {}
    for s in _ORDEM_SETORES:
        if s in agrupado:
            resultado[s] = agrupado[s]
    for s in agrupado:
        if s not in resultado:
            resultado[s] = agrupado[s]
    return resultado
