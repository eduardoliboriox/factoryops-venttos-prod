### Objetivo - (tarefas para você executar, aplicando com CLAUDE.md)

### 1. Webscryping
* a eempresa tem um sistema / site, tudo local, onde a produção fica lançamento, input, quero aproveitar os dados para usar no meu sistema, vai ser util na parte de PCP, extrair a produção por dia, modelo, turno, precisa de ajudar pra fazer a primeira vez com isto
USUARIO = "user1"
SENHA   = "123456"

me ajude a gerar os arquivo e tudo que precisa.,

API: http://192.168.1.35:5000/api/producao
Retorna array direto (sem paginação no JSON — provavelmente filtra por data)
Campos: id, data, setor, linha, modelos, familia, turno, producao_real, qtd_perda, quantidade_defeitos, intervalo_tempo, inicio, final

Agora vou montar o projeto completo e funcional:Executou 3 comandos, criou 3 arquivos, leu um arquivoExecutou 3 comandos, criou 3 arquivos, leu um arquivoPronto! O projeto está completo. Aqui está o que você faz:
1. Instalar e rodar:
bashpip install -r requirements.txt
python coletor.py
2. Editar as credenciais no topo do coletor.py:

3. USUARIO = "seu_usuario"
SENHA   = "sua_senha"
```

**3. Usar no seu PCP:**
```
# Todos os registros de um período
GET http://localhost:5001/api/producao?dataInicial=2026-03-01&dataFinal=2026-03-20

# Hora a hora de hoje (o que você mais precisa)
GET http://localhost:5001/api/producao/hora-a-hora?dataInicial=2026-03-20&dataFinal=2026-03-20

# Só um setor
GET http://localhost:5001/api/producao/hora-a-hora?dataInicial=2026-03-20&dataFinal=2026-03-20&setor=PTH

# Resumo agregado por linha
GET http://localhost:5001/api/producao/resumo?dataInicial=2026-03-01&dataFinal=2026-03-20

"""
PCP Venttos - Coletor de Produção
Bate direto na API interna do Input BI e expõe os dados via Flask.

Uso:
    python coletor.py

Endpoints disponíveis:
    GET /api/producao?dataInicial=2026-03-01&dataFinal=2026-03-20
    GET /api/producao/hoje
    GET /api/producao/resumo?dataInicial=...&dataFinal=...
    GET /api/status
"""

import requests
import json
from datetime import datetime, date, timedelta
from flask import Flask, jsonify, request

# ─────────────────────────────────────────────
# CONFIGURAÇÃO — ajuste aqui se mudar
# ─────────────────────────────────────────────
VENTTOS_BASE   = "http://192.168.1.35:5000"
VENTTOS_LOGIN  = f"{VENTTOS_BASE}/api/login"      # ajuste se a rota for diferente
VENTTOS_API    = f"{VENTTOS_BASE}/api/producao"
USUARIO        = "seu_usuario"                     # ← coloque aqui
SENHA          = "sua_senha"                       # ← coloque aqui
PORTA_PCP      = 5001
# ─────────────────────────────────────────────

app = Flask(__name__)
_sessao = requests.Session()
_logado = False


def fazer_login():
    """Autentica no Venttos e mantém o cookie de sessão."""
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
        else:
            print(f"[{_agora()}] Falha no login: {resp.status_code} — {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"[{_agora()}] Erro no login: {e}")
        return False


def buscar_producao(data_inicial: str, data_final: str) -> list:
    """
    Busca registros de produção no Venttos.
    
    data_inicial / data_final: formato YYYY-MM-DD
    Retorna lista de dicts com os campos normalizados.
    """
    global _logado

    if not _logado:
        if not fazer_login():
            return []

    params = {
        "dataInicial": data_inicial,
        "dataFinal":   data_final,
        # sem setor, sem linha → traz tudo
    }

    try:
        resp = _sessao.get(VENTTOS_API, params=params, timeout=30)

        # Se retornou 401/403, tenta relogar uma vez
        if resp.status_code in (401, 403):
            print(f"[{_agora()}] Sessão expirada, refazendo login...")
            _logado = False
            if fazer_login():
                resp = _sessao.get(VENTTOS_API, params=params, timeout=30)

        resp.raise_for_status()
        dados_brutos = resp.json()

        # Normaliza cada registro
        return [_normalizar(r) for r in dados_brutos]

    except Exception as e:
        print(f"[{_agora()}] Erro ao buscar produção: {e}")
        return []


def _normalizar(r: dict) -> dict:
    """Transforma o registro bruto do Venttos no formato limpo pro PCP."""
    # Data: "2026-03-20T00:00:00.000Z" → "2026-03-20"
    data_str = r.get("data", "")[:10] if r.get("data") else ""

    # Hora início/fim: "1970-01-01T21:00:00.000Z" → "21:00"
    inicio = _extrair_hora(r.get("inicio", ""))
    fim    = _extrair_hora(r.get("final", ""))

    return {
        "id":               r.get("id"),
        "data":             data_str,
        "setor":            r.get("setor", ""),
        "linha":            r.get("linha", ""),
        "turno":            r.get("turno", ""),
        "semana":           r.get("semana"),
        "modelo":           r.get("modelos", ""),
        "familia":          r.get("familia", ""),
        "hora_inicio":      inicio,
        "hora_fim":         fim,
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
    """'1970-01-01T21:00:00.000Z' → '21:00'"""
    if not iso:
        return ""
    try:
        return iso[11:16]  # pega só HH:MM
    except Exception:
        return iso


def _agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _resumir(registros: list) -> dict:
    """Gera um resumo agregado por setor/linha."""
    resumo = {}
    for r in registros:
        chave = f"{r['setor']} | {r['linha']}"
        if chave not in resumo:
            resumo[chave] = {
                "setor":         r["setor"],
                "linha":         r["linha"],
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
# ENDPOINTS FLASK
# ─────────────────────────────────────────────

@app.route("/api/producao", methods=["GET"])
def producao():
    """
    Retorna todos os registros no período.
    Params: dataInicial (YYYY-MM-DD), dataFinal (YYYY-MM-DD)
    Opcional: setor, linha, turno (filtra localmente após buscar)
    """
    data_inicial = request.args.get("dataInicial", str(date.today()))
    data_final   = request.args.get("dataFinal",   str(date.today()))
    setor        = request.args.get("setor", "").upper()
    linha        = request.args.get("linha", "").upper()
    turno        = request.args.get("turno", "")

    dados = buscar_producao(data_inicial, data_final)

    # Filtros opcionais locais
    if setor:
        dados = [d for d in dados if d["setor"].upper() == setor]
    if linha:
        dados = [d for d in dados if d["linha"].upper() == linha]
    if turno:
        dados = [d for d in dados if turno.lower() in d["turno"].lower()]

    return jsonify({
        "data_inicial":  data_inicial,
        "data_final":    data_final,
        "total":         len(dados),
        "coletado_em":   _agora(),
        "dados":         dados
    })


@app.route("/api/producao/hoje", methods=["GET"])
def producao_hoje():
    """Atalho: retorna a produção de hoje."""
    hoje = str(date.today())
    dados = buscar_producao(hoje, hoje)
    return jsonify({
        "data":        hoje,
        "total":       len(dados),
        "coletado_em": _agora(),
        "dados":       dados
    })


@app.route("/api/producao/resumo", methods=["GET"])
def resumo():
    """
    Retorna produção agregada por setor/linha no período.
    Útil pra dashboards e relatórios do PCP.
    """
    data_inicial = request.args.get("dataInicial", str(date.today()))
    data_final   = request.args.get("dataFinal",   str(date.today()))

    dados   = buscar_producao(data_inicial, data_final)
    agrupado = _resumir(dados)

    producao_total = sum(r["producao_total"] for r in agrupado)
    perda_total    = sum(r["perda_total"]    for r in agrupado)
    defeitos_total = sum(r["defeitos_total"] for r in agrupado)

    return jsonify({
        "data_inicial":    data_inicial,
        "data_final":      data_final,
        "coletado_em":     _agora(),
        "producao_total":  producao_total,
        "perda_total":     perda_total,
        "defeitos_total":  defeitos_total,
        "linhas_ativas":   len(agrupado),
        "por_linha":       agrupado
    })


@app.route("/api/producao/hora-a-hora", methods=["GET"])
def hora_a_hora():
    """
    Retorna produção agrupada por hora.
    Ideal pra gráfico hora-hora no PCP.
    Params: dataInicial, dataFinal, setor (opcional), linha (opcional)
    """
    data_inicial = request.args.get("dataInicial", str(date.today()))
    data_final   = request.args.get("dataFinal",   str(date.today()))
    setor        = request.args.get("setor", "").upper()
    linha        = request.args.get("linha", "").upper()

    dados = buscar_producao(data_inicial, data_final)

    if setor:
        dados = [d for d in dados if d["setor"].upper() == setor]
    if linha:
        dados = [d for d in dados if d["linha"].upper() == linha]

    # Agrupa por hora de início
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
        "data_inicial":  data_inicial,
        "data_final":    data_final,
        "coletado_em":   _agora(),
        "total_horas":   len(ordenado),
        "hora_a_hora":   ordenado
    })


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "ok":          True,
        "logado":      _logado,
        "servidor":    VENTTOS_BASE,
        "hora_atual":  _agora()
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
