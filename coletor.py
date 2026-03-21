"""
PCP Venttos - Coletor de Produção
Bate direto na API interna do Input BI e expõe os dados via Flask.

Uso:
    python coletor.py

Endpoints disponíveis:
    GET /api/producao?dataInicial=2026-03-01&dataFinal=2026-03-20
    GET /api/producao/hoje
    GET /api/producao/resumo?dataInicial=...&dataFinal=...
    GET /api/producao/hora-a-hora?dataInicial=...&dataFinal=...
    GET /api/status
"""

import requests
from datetime import datetime, date
from flask import Flask, jsonify, request

# ─────────────────────────────────────────────
# CONFIGURAÇÃO — ajuste aqui se mudar
# ─────────────────────────────────────────────
VENTTOS_BASE  = "http://192.168.1.35:5000"
VENTTOS_LOGIN = f"{VENTTOS_BASE}/api/login"
VENTTOS_API   = f"{VENTTOS_BASE}/api/producao"
USUARIO       = "user1"
SENHA         = "123456"
PORTA_PCP     = 5001
# ─────────────────────────────────────────────

app = Flask(__name__)
_sessao = requests.Session()
_logado = False


def _agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fazer_login() -> bool:
    global _logado
    try:
        resp = _sessao.post(VENTTOS_LOGIN, json={
            "username": USUARIO,
            "password": SENHA
        }, timeout=10)
        if resp.status_code in (200, 201):
            _logado = True
            print(f"[{_agora()}] Login OK")
            return True
        print(f"[{_agora()}] Falha no login: {resp.status_code} — {resp.text[:200]}")
        return False
    except Exception as e:
        print(f"[{_agora()}] Erro no login: {e}")
        return False


def buscar_producao(data_inicial: str, data_final: str) -> list:
    global _logado

    if not _logado:
        if not fazer_login():
            return []

    params = {"dataInicial": data_inicial, "dataFinal": data_final}

    try:
        resp = _sessao.get(VENTTOS_API, params=params, timeout=30)

        if resp.status_code in (401, 403):
            print(f"[{_agora()}] Sessão expirada, refazendo login...")
            _logado = False
            if fazer_login():
                resp = _sessao.get(VENTTOS_API, params=params, timeout=30)

        resp.raise_for_status()
        return [_normalizar(r) for r in resp.json()]

    except Exception as e:
        print(f"[{_agora()}] Erro ao buscar produção: {e}")
        return []


def _normalizar(r: dict) -> dict:
    data_str = r.get("data", "")[:10] if r.get("data") else ""
    return {
        "id":               r.get("id"),
        "data":             data_str,
        "setor":            r.get("setor", ""),
        "linha":            r.get("linha", ""),
        "turno":            r.get("turno", ""),
        "semana":           r.get("semana"),
        "modelo":           r.get("modelos", ""),
        "familia":          r.get("familia", ""),
        "hora_inicio":      _extrair_hora(r.get("inicio", "")),
        "hora_fim":         _extrair_hora(r.get("final", "")),
        "intervalo":        r.get("intervalo_tempo", ""),
        "producao_real":    r.get("producao_real", 0),
        "qtd_perda":        r.get("qtd_perda", 0),
        "defeitos":         r.get("quantidade_defeitos", 0),
        "parada_seg":       r.get("parada_em_seg"),
        "codigo_parada":    r.get("codigo_de_parada"),
        "descricao_parada": r.get("descricao_da_parada"),
        "observacao":       r.get("observacao"),
    }


def _extrair_hora(iso: str) -> str:
    if not iso:
        return ""
    try:
        return iso[11:16]
    except Exception:
        return iso


def _resumir(registros: list) -> list:
    resumo = {}
    for r in registros:
        chave = f"{r['setor']} | {r['linha']}"
        if chave not in resumo:
            resumo[chave] = {
                "setor":          r["setor"],
                "linha":          r["linha"],
                "producao_total": 0,
                "perda_total":    0,
                "defeitos_total": 0,
                "registros":      0,
            }
        resumo[chave]["producao_total"] += r["producao_real"] or 0
        resumo[chave]["perda_total"]    += r["qtd_perda"] or 0
        resumo[chave]["defeitos_total"] += r["defeitos"] or 0
        resumo[chave]["registros"]      += 1
    return list(resumo.values())


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.route("/api/producao", methods=["GET"])
def producao():
    data_inicial = request.args.get("dataInicial", str(date.today()))
    data_final   = request.args.get("dataFinal",   str(date.today()))
    setor        = request.args.get("setor", "").upper()
    linha        = request.args.get("linha", "").upper()
    turno        = request.args.get("turno", "")

    dados = buscar_producao(data_inicial, data_final)

    if setor:
        dados = [d for d in dados if d["setor"].upper() == setor]
    if linha:
        dados = [d for d in dados if d["linha"].upper() == linha]
    if turno:
        dados = [d for d in dados if turno.lower() in d["turno"].lower()]

    return jsonify({
        "data_inicial": data_inicial,
        "data_final":   data_final,
        "total":        len(dados),
        "coletado_em":  _agora(),
        "dados":        dados,
    })


@app.route("/api/producao/hoje", methods=["GET"])
def producao_hoje():
    hoje = str(date.today())
    dados = buscar_producao(hoje, hoje)
    return jsonify({
        "data":        hoje,
        "total":       len(dados),
        "coletado_em": _agora(),
        "dados":       dados,
    })


@app.route("/api/producao/resumo", methods=["GET"])
def resumo():
    data_inicial = request.args.get("dataInicial", str(date.today()))
    data_final   = request.args.get("dataFinal",   str(date.today()))

    dados    = buscar_producao(data_inicial, data_final)
    agrupado = _resumir(dados)

    return jsonify({
        "data_inicial":   data_inicial,
        "data_final":     data_final,
        "coletado_em":    _agora(),
        "producao_total": sum(r["producao_total"] for r in agrupado),
        "perda_total":    sum(r["perda_total"]    for r in agrupado),
        "defeitos_total": sum(r["defeitos_total"] for r in agrupado),
        "linhas_ativas":  len(agrupado),
        "por_linha":      agrupado,
    })


@app.route("/api/producao/hora-a-hora", methods=["GET"])
def hora_a_hora():
    data_inicial = request.args.get("dataInicial", str(date.today()))
    data_final   = request.args.get("dataFinal",   str(date.today()))
    setor        = request.args.get("setor", "").upper()
    linha        = request.args.get("linha", "").upper()

    dados = buscar_producao(data_inicial, data_final)

    if setor:
        dados = [d for d in dados if d["setor"].upper() == setor]
    if linha:
        dados = [d for d in dados if d["linha"].upper() == linha]

    por_hora = {}
    for r in dados:
        hora = r["hora_inicio"] or "??"
        if hora not in por_hora:
            por_hora[hora] = {"hora": hora, "producao": 0, "perda": 0, "defeitos": 0, "registros": 0}
        por_hora[hora]["producao"]  += r["producao_real"] or 0
        por_hora[hora]["perda"]     += r["qtd_perda"] or 0
        por_hora[hora]["defeitos"]  += r["defeitos"] or 0
        por_hora[hora]["registros"] += 1

    ordenado = sorted(por_hora.values(), key=lambda x: x["hora"])

    return jsonify({
        "data_inicial": data_inicial,
        "data_final":   data_final,
        "coletado_em":  _agora(),
        "total_horas":  len(ordenado),
        "hora_a_hora":  ordenado,
    })


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "ok":         True,
        "logado":     _logado,
        "servidor":   VENTTOS_BASE,
        "hora_atual": _agora(),
    })


# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  PCP Venttos - Coletor de Produção")
    print("=" * 50)
    print(f"  Conectando em: {VENTTOS_BASE}")
    fazer_login()
    print(f"  API rodando em: http://localhost:{PORTA_PCP}")
    print()
    app.run(host="0.0.0.0", port=PORTA_PCP, debug=False)
