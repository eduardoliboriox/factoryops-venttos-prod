"""
PCP Venttos - Coletor de Produção
Busca dados da API interna do Input BI (sem autenticação) e salva no banco Railway.

Uso:
    python coletor.py --de 2026-03-01 --ate 2026-03-20
        → coleta e salva direto no banco (PC precisa de internet)

    python coletor.py --de 2026-03-01 --ate 2026-03-20 --json dados.json
        → coleta e salva em arquivo local (usar quando sem internet)

    python coletor.py --importar dados.json
        → lê o arquivo e salva no banco (rodar no PC com internet)

Variáveis de ambiente necessárias (arquivo .env ou ambiente):
    DATABASE_URL     → string de conexão PostgreSQL Railway
    VENTTOS_API_URL  → URL base da API local (padrão: http://192.168.1.35:5000/api/producao)
"""

import os
import sys
import json
import requests
import psycopg
from datetime import datetime, date

from dotenv import load_dotenv
load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURAÇÃO — lida do ambiente
# ─────────────────────────────────────────────
VENTTOS_API  = os.environ.get("VENTTOS_API_URL", "http://192.168.1.35:5000/api/producao")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
# ─────────────────────────────────────────────


def _agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def buscar_producao(data_inicial: str, data_final: str) -> list:
    params = {"dataInicial": data_inicial, "dataFinal": data_final}
    try:
        resp = requests.get(VENTTOS_API, params=params, timeout=30)
        resp.raise_for_status()
        todos = [_normalizar(r) for r in resp.json()]
        return [r for r in todos if _data_no_intervalo(r["data"], data_inicial, data_final)]
    except Exception as e:
        print(f"[{_agora()}] Erro ao buscar produção: {e}")
        return []


def _data_no_intervalo(data: str, data_inicial: str, data_final: str) -> bool:
    if not data:
        return False
    return data_inicial <= data <= data_final


def _normalizar(r: dict) -> dict:
    data_str = r.get("data", "")[:10] if r.get("data") else ""
    return {
        "id":               r.get("id"),
        "data":             data_str or None,
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


def salvar_no_banco(registros: list) -> int:
    if not registros:
        return 0
    if not DATABASE_URL:
        print(f"[{_agora()}] Erro: DATABASE_URL não configurada. Defina no arquivo .env.")
        return 0

    salvos = 0
    try:
        with psycopg.connect(DATABASE_URL, sslmode="require") as conn:
            with conn.cursor() as cur:
                for r in registros:
                    cur.execute("""
                        INSERT INTO producao_coletada (
                            id, data, setor, linha, turno, semana, modelo, familia,
                            hora_inicio, hora_fim, intervalo, producao_real, qtd_perda,
                            defeitos, parada_seg, codigo_parada, descricao_parada,
                            observacao, coletado_em
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, NOW()
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            producao_real    = EXCLUDED.producao_real,
                            qtd_perda        = EXCLUDED.qtd_perda,
                            defeitos         = EXCLUDED.defeitos,
                            descricao_parada = EXCLUDED.descricao_parada,
                            observacao       = EXCLUDED.observacao,
                            coletado_em      = NOW()
                    """, (
                        r["id"], r["data"], r["setor"], r["linha"], r["turno"],
                        r["semana"], r["modelo"], r["familia"],
                        r["hora_inicio"], r["hora_fim"], r["intervalo"],
                        r["producao_real"], r["qtd_perda"],
                        r["defeitos"], r["parada_seg"], r["codigo_parada"],
                        r["descricao_parada"], r["observacao"],
                    ))
                    salvos += 1

        print(f"[{_agora()}] Banco: {salvos} registros salvos/atualizados.")
        return salvos

    except Exception as e:
        print(f"[{_agora()}] Erro ao salvar no banco: {e}")
        return 0


# ─────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    print("=" * 50)
    print("  PCP Venttos - Coletor de Produção")
    print("=" * 50)

    # Modo: importar de arquivo JSON para o banco
    if "--importar" in args:
        arquivo = args[args.index("--importar") + 1]
        print(f"  Lendo: {arquivo}")
        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
        print(f"  Registros no arquivo: {len(dados)}")
        print(f"  Salvos: {salvar_no_banco(dados)}")
        sys.exit(0)

    # Modo: coleta por data única
    if "--data" in args:
        data  = args[args.index("--data") + 1]
        dados = buscar_producao(data, data)
        print(f"  Buscados: {len(dados)} registros para {data}")
        if "--json" in args:
            arquivo = args[args.index("--json") + 1]
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, default=str)
            print(f"  Salvo em arquivo: {arquivo}")
        else:
            print(f"  Salvos no banco: {salvar_no_banco(dados)}")
        sys.exit(0)

    # Modo: coleta por intervalo
    if "--de" in args and "--ate" in args:
        de   = args[args.index("--de")  + 1]
        ate  = args[args.index("--ate") + 1]
        dados = buscar_producao(de, ate)
        print(f"  Buscados: {len(dados)} registros de {de} a {ate}")
        if "--json" in args:
            arquivo = args[args.index("--json") + 1]
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, default=str)
            print(f"  Salvo em arquivo: {arquivo}")
        else:
            print(f"  Salvos no banco: {salvar_no_banco(dados)}")
        sys.exit(0)

    # Modo padrão: coleta hoje e salva no banco
    hoje  = str(date.today())
    dados = buscar_producao(hoje, hoje)
    print(f"  Coletados hoje: {len(dados)} registros")
    salvar_no_banco(dados)
