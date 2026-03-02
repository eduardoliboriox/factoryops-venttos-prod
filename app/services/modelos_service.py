import math
import time

from app.repositories import modelos_repository
from app.repositories.modelos_repository import buscar_ultimo_modelo


LINHAS_VALIDAS = {
    "SMD-01", "SMD-02", "SMD-03", "SMD-04", "SMD-05",
    "SMD-06", "SMD-07", "SMD-08", "SMD-09"
}

_MODELOS_CACHE_TTL_SECONDS = 10
_modelos_cache_value = None
_modelos_cache_expires_at = 0.0


def _cache_get():
    global _modelos_cache_value, _modelos_cache_expires_at
    now = time.time()
    if _modelos_cache_value is not None and now < _modelos_cache_expires_at:
        return _modelos_cache_value
    return None


def _cache_set(value):
    global _modelos_cache_value, _modelos_cache_expires_at
    _modelos_cache_value = value
    _modelos_cache_expires_at = time.time() + _MODELOS_CACHE_TTL_SECONDS


def _cache_invalidate():
    global _modelos_cache_value, _modelos_cache_expires_at
    _modelos_cache_value = None
    _modelos_cache_expires_at = 0.0


def resumo_dashboard():
    modelos = modelos_repository.listar_modelos()

    total = len(modelos)

    por_setor = {}
    por_fase = {}

    for m in modelos:
        setor = m.get("setor")
        fase = m.get("fase")

        if setor:
            por_setor[setor] = por_setor.get(setor, 0) + 1

        if fase:
            por_fase[fase] = por_fase.get(fase, 0) + 1

    ultimo_modelo = buscar_ultimo_modelo()

    return {
        "total_modelos": total,
        "por_setor": por_setor,
        "por_fase": por_fase,
        "ultimo_modelo": ultimo_modelo
    }


def listar_codigos():
    return modelos_repository.listar_codigos()


def _to_float_2(v):
    if v is None or v == "":
        return None
    try:
        return round(float(v), 2)
    except Exception:
        return None


def listar():
    cached = _cache_get()
    if cached is not None:
        return cached

    modelos = modelos_repository.listar_modelos()

    payload = [
        {
            "codigo": m.get("codigo"),
            "cliente": m.get("cliente"),
            "setor": m.get("setor"),
            "linha": m.get("linha"),
            "meta": float(m["meta_padrao"]) if m.get("meta_padrao") is not None else 0,
            "tempo_montagem": _to_float_2(m.get("tempo_montagem")),
            "blank": m.get("blank"),
            "fase": m.get("fase")
        }
        for m in (modelos or [])
    ]

    _cache_set(payload)
    return payload


def listar_modelos():
    return listar()


def cadastrar_modelo(dados):
    linha = (dados.get("linha") or "").strip()
    if not linha:
        return {"sucesso": False, "mensagem": "Linha não informada"}
    if linha not in LINHAS_VALIDAS:
        return {"sucesso": False, "mensagem": "Linha inválida"}

    try:
        modelos_repository.inserir(dados)
        _cache_invalidate()
        return {"sucesso": True, "mensagem": "Modelo cadastrado"}
    except Exception as e:
        print("ERRO AO CADASTRAR:", e)
        return {"sucesso": False, "mensagem": str(e)}


def excluir_modelo(dados):
    codigo = (dados.get("codigo") or "").strip()
    fase = (dados.get("fase") or "").strip()
    linha = (dados.get("linha") or "").strip()

    if not codigo or not fase or not linha:
        return {"sucesso": False, "mensagem": "Código, fase e linha são obrigatórios"}

    try:
        modelos_repository.excluir(codigo, fase, linha)
        _cache_invalidate()
        return {"sucesso": True, "mensagem": "Modelo excluído com sucesso"}
    except Exception as e:
        print("ERRO AO EXCLUIR:", e)
        return {"sucesso": False, "mensagem": "Erro ao excluir modelo"}


def atualizar_modelo(dados):
    codigo = (dados.get("codigo") or "").strip()
    fase = (dados.get("fase") or "").strip()
    linha = (dados.get("linha") or "").strip()

    if not codigo or not fase or not linha:
        return {"sucesso": False, "mensagem": "Código, fase e linha são obrigatórios"}

    campos = {}

    if dados.get("meta_padrao"):
        campos["meta_padrao"] = float(dados["meta_padrao"])

    if dados.get("tempo_montagem"):
        campos["tempo_montagem"] = float(dados["tempo_montagem"])

    if dados.get("blank"):
        campos["blank"] = int(dados["blank"])

    if dados.get("novo_codigo"):
        campos["codigo"] = str(dados["novo_codigo"]).strip()

    if not campos:
        return {"sucesso": False, "mensagem": "Nada para atualizar"}

    try:
        modelos_repository.atualizar(codigo, fase, linha, campos)
        _cache_invalidate()
        return {"sucesso": True, "mensagem": "Modelo atualizado"}
    except Exception as e:
        print("ERRO AO ATUALIZAR:", e)
        return {"sucesso": False, "mensagem": "Erro ao atualizar modelo"}


def calcular_meta(dados):
    meta = float(dados["meta_padrao"])
    pessoas_atual = int(dados["pessoas_atuais"])
    pessoas_padrao = int(dados["pessoas_padrao"])
    minutos = int(dados["minutos"])

    meta_ajustada = round(
        meta * (pessoas_atual / pessoas_padrao) * 0.85
    )

    qtd = round(meta_ajustada * (minutos / 60))

    return {"resultado": f"{minutos} min → {qtd} peças"}


def calcular_perda_producao(meta_hora, producao_real):
    meta_hora = float(meta_hora)
    producao_real = float(producao_real)

    if meta_hora <= 0:
        return {"erro": "Meta inválida"}

    if producao_real >= meta_hora:
        return {"tempo_perdido": "0 minutos e 00 segundos", "pecas_faltantes": 0}

    minutos_por_peca = 60 / meta_hora
    tempo_produzido = producao_real * minutos_por_peca
    tempo_perdido = 60 - tempo_produzido

    minutos = int(tempo_perdido)
    segundos = int(round((tempo_perdido - minutos) * 60))

    if segundos == 60:
        minutos += 1
        segundos = 0

    return {
        "tempo_perdido": f"{minutos} minutos e {segundos:02d} segundos",
        "pecas_faltantes": int(meta_hora - producao_real)
    }


def calcular_meta_smt(tempo_montagem, blank):
    tempo = float(tempo_montagem)
    blank = int(blank)

    if tempo <= 0 or blank <= 0:
        return {"sucesso": False, "erro": "Valores inválidos"}

    meta_teorica_blanks_float = 3600 / tempo
    meta_teorica_blanks_int = math.floor(meta_teorica_blanks_float)
    meta_teorica_placas_int = meta_teorica_blanks_int * blank

    meta_com_perda_blanks = meta_teorica_blanks_float * 0.9
    meta_com_perda_placas = meta_com_perda_blanks * blank

    meta_final = math.floor(meta_com_perda_placas / blank) * blank

    return {
        "sucesso": True,
        "dados": {
            "meta_hora": meta_final,
            "meta_teorica_blanks": meta_teorica_blanks_int,
            "meta_teorica_placas": meta_teorica_placas_int,
            "meta_com_perda": round(meta_com_perda_placas, 2)
        }
    }


def calcular_tempo_smt_inverso(meta_hora, blank):
    try:
        meta = float(meta_hora)
        blank = int(blank)

        if meta <= 0 or blank <= 0:
            return {"sucesso": False, "erro": "Valores inválidos"}

        tempo = (3600 * 0.9 * blank) / meta

        return {"sucesso": True, "dados": {"tempo_montagem": round(tempo, 2)}}
    except Exception:
        return {"sucesso": False, "erro": "Erro no cálculo inverso"}


def calculo_rapido(meta_hora, minutos, blank=None):
    meta_hora = float(meta_hora)
    minutos = float(minutos)

    placas = (meta_hora / 60) * minutos

    if not blank or float(blank) <= 1:
        return {"placas": round(placas, 2)}

    blank = int(blank)
    blanks = math.floor(placas / blank)

    return {"blanks": blanks, "placas_reais": blanks * blank}
