"""
PCP Venttos - Coletor MES (Sumário de Produção)
Chama a API interna do MES diretamente via POST — sem scraping, sem browser.

Uso:
    python coletor_mes.py                                    (coleta hoje)
    python coletor_mes.py --data 2026-04-28
    python coletor_mes.py --de 2026-04-01 --ate 2026-04-28
    python coletor_mes.py --de 2026-04-01 --ate 2026-04-28 --filial VTE
    python coletor_mes.py --de 2026-04-01 --ate 2026-04-28 --json coletas/mes/mes.json
    python coletor_mes.py --importar coletas/mes/mes.json
    python coletor_mes.py --sniff                     (inspeciona chamadas de rede da pagina)
    python coletor_mes.py --sniff --data 2026-04-29   (sniff para data especifica)
    python coletor_mes.py --debug                     (browser visivel para diagnostico)

Variaveis de ambiente (.env):
    DATABASE_URL  -> string de conexao PostgreSQL Railway
    MES_URL       -> URL base do sistema MES (padrao: http://192.168.1.32)
    MES_USUARIO   -> usuario de login (necessario apenas para --debug e --sniff)
    MES_SENHA     -> senha de login   (necessario apenas para --debug e --sniff)
"""

import os
import sys
import json
import hashlib
import re
import requests
import psycopg
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

from dotenv import load_dotenv
load_dotenv()

MES_URL      = os.environ.get("MES_URL", "http://192.168.1.32")
MES_USUARIO  = os.environ.get("MES_USUARIO", "")
MES_SENHA    = os.environ.get("MES_SENHA", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

COLETAS_DIR = "coletas/mes"


def _salvar_json(arquivo: str, dados: list) -> None:
    dirname = os.path.normpath(os.path.dirname(arquivo)) if os.path.dirname(arquivo) else ""
    if not dirname or dirname == "coletas":
        arquivo = os.path.join(COLETAS_DIR, os.path.basename(arquivo))
    os.makedirs(os.path.dirname(arquivo), exist_ok=True)
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, default=str)
    print(f"  Salvo em: {arquivo}")

FILIAIS_VALIDAS = {"VTE", "VTT"}
SUMARIO_URL     = f"{MES_URL}/sfc/relatorios/linha"
API_RELATORIO   = f"{MES_URL}/sfc-back/api/relatorio"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _gerar_id(data: str, linha: str, turno: str, produto: str) -> int:
    key = f"mes-sum|{data}|{linha}|{turno}|{produto}"
    digest = hashlib.md5(key.encode()).hexdigest()
    return int(digest[:8], 16) % 1_000_000_000 + 1_000_000_001


def _calcular_semana(data_iso: str) -> int | None:
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").isocalendar()[1]
    except Exception:
        return None


def _to_int(s: str) -> int:
    try:
        return int(float(str(s).replace(",", ".").strip()))
    except (ValueError, AttributeError):
        return 0


def _extrair_turno(texto: str) -> str:
    t = texto.upper()
    if re.search(r"3[°º]?\s*T", t) or "3° TURNO" in t or "3°TURNO" in t:
        return "3º Turno"
    if re.search(r"2[°º]?\s*T", t) or "2° TURNO" in t or "2°TURNO" in t:
        return "2º Turno"
    if re.search(r"1[°º]?\s*T", t) or "1° TURNO" in t or "1°TURNO" in t:
        return "1º Turno"
    return ""


def _extrair_filial_linha(texto: str) -> tuple[str, str] | None:
    """Extrai (filial, linha) de 'VTE - PA-10', 'VTT-IPCOM', etc."""
    texto = texto.strip()
    if " - " in texto:
        partes = texto.split(" - ", 1)
        filial = partes[0].strip()
        linha  = partes[1].strip()
    else:
        for f in FILIAIS_VALIDAS:
            if texto.startswith(f + "-"):
                filial = f
                linha  = texto[len(f) + 1:]
                break
        else:
            return None
    if filial not in FILIAIS_VALIDAS:
        return None
    return filial, linha


def _extrair_turno_api(turno_str: str) -> str:
    """Extrai '1º Turno' / '2º Turno' / '3º Turno' do campo Turno da API (ex: '00001|VTE-1T-SMD')."""
    m = re.search(r"(\d)T", turno_str, re.IGNORECASE)
    if m:
        return f"{m.group(1)}º Turno"
    return _extrair_turno(turno_str)


def _carregar_mapa_setores() -> dict:
    if not DATABASE_URL:
        return {}
    try:
        with psycopg.connect(DATABASE_URL, sslmode="require") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT linha, setor FROM linha_config")
                return {row[0]: row[1] for row in cur.fetchall()}
    except Exception as e:
        print(f"[{_agora()}] Aviso: nao foi possivel carregar mapa de setores: {e}")
        return {}


# ─── Playwright: login ────────────────────────────────────────────────────────

def _aguardar_vue(page: Page, timeout: int = 12000) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except PWTimeout:
        pass
    page.wait_for_timeout(2500)


def _fazer_login(page: Page) -> bool:
    try:
        page.goto(SUMARIO_URL, timeout=20000)
        page.wait_for_load_state("domcontentloaded")

        user_sel = "input[type='text'], input[type='email'], input[name*='user' i], input[id*='user' i]"
        page.wait_for_selector(user_sel, timeout=10000)
        page.fill(user_sel, MES_USUARIO)
        page.fill("input[type='password']", MES_SENHA)
        page.click("button[type='submit'], input[type='submit']")
        page.wait_for_load_state("networkidle", timeout=20000)

        if "/Account/Login" in page.url:
            print(f"[{_agora()}] Falha no login MES: credenciais invalidas.")
            return False

        print(f"[{_agora()}] Login MES OK. URL: {page.url}")
        return True

    except PWTimeout:
        print(f"[{_agora()}] Timeout no login MES.")
        return False
    except Exception as e:
        print(f"[{_agora()}] Erro no login MES: {e}")
        return False


# ─── Playwright: navegação e coleta ──────────────────────────────────────────

def _navegar_para_sumario(page: Page) -> bool:
    """Navega para /sfc/relatorios/linha. Tenta goto direto; fallback pelo sidebar."""
    if "relatorios/linha" not in page.url:
        try:
            page.goto(SUMARIO_URL, timeout=20000)
            _aguardar_vue(page)
        except PWTimeout:
            pass

    if "relatorios/linha" in page.url:
        return True

    print(f"[{_agora()}] Goto direto nao funcionou. Navegando pelo sidebar...")
    try:
        _aguardar_vue(page)

        TENTATIVAS = [
            ("text=Relatórios", "text=Linha"),
            ("text=Relatórios", "text=Sumário"),
            ("text=Relatórios", "text=Sumario"),
            ("text=Relatórios", "text=Produção"),
            ("text=Relatório",  "text=Linha"),
        ]

        for sel_pai, sel_filho in TENTATIVAS:
            try:
                page.click(sel_pai, timeout=6000)
                page.wait_for_timeout(800)
                page.click(sel_filho, timeout=6000)
                _aguardar_vue(page)
                if "relatorios/linha" in page.url:
                    return True
            except PWTimeout:
                continue

        return "relatorios/linha" in page.url

    except Exception as e:
        print(f"[{_agora()}] Erro ao navegar para sumario: {e}")
        return False


MESES_BR = {
    1: ["janeiro", "jan"], 2: ["fevereiro", "fev"], 3: ["março", "mar", "marco"],
    4: ["abril", "abr"],   5: ["maio", "mai"],      6: ["junho", "jun"],
    7: ["julho", "jul"],   8: ["agosto", "ago"],    9: ["setembro", "set"],
    10: ["outubro", "out"], 11: ["novembro", "nov"], 12: ["dezembro", "dez"],
}


def _mes_ano_do_header(texto: str) -> tuple[int, int] | None:
    """Extrai (mes, ano) do texto do header do calendário Vuetify."""
    texto = texto.lower().strip()
    ano_match = re.search(r"\b(20\d{2})\b", texto)
    if not ano_match:
        return None
    ano = int(ano_match.group(1))
    for mes_num, nomes in MESES_BR.items():
        if any(nome in texto for nome in nomes):
            return mes_num, ano
    return None


def _selecionar_data_calendario(page: Page, data_iso: str) -> bool:
    """
    Abre o Vuetify date picker, navega até o mês correto e clica no dia.
    Funciona mesmo que o calendário esteja em um mês diferente do alvo.
    """
    dt         = datetime.strptime(data_iso, "%Y-%m-%d")
    target_dia = str(dt.day)

    inputs = page.query_selector_all("input[type='text'], input[type='date']")
    if not inputs:
        return False
    inputs[0].click()

    try:
        page.wait_for_selector(".v-date-picker-table, .v-picker__body", timeout=8000)
    except PWTimeout:
        return False
    page.wait_for_timeout(400)

    for _ in range(24):
        header_el = page.query_selector(
            ".v-date-picker-header__value button, "
            ".v-date-picker-header .v-btn:not(.v-btn--icon)"
        )
        header_text = header_el.inner_text().strip() if header_el else ""
        parsed      = _mes_ano_do_header(header_text)

        if parsed:
            mes_atual, ano_atual = parsed
            diff = (dt.year - ano_atual) * 12 + (dt.month - mes_atual)
            if diff == 0:
                break
            btn_nav = page.query_selector(
                ".v-date-picker-header button:last-child" if diff > 0
                else ".v-date-picker-header button:first-child"
            )
            if btn_nav:
                btn_nav.click()
                page.wait_for_timeout(300)
        else:
            break

    # Clica no dia correto (ignora botoes desabilitados = dias de outro mes)
    buttons = page.query_selector_all(
        ".v-date-picker-table--date button:not([disabled]):not(.v-btn--disabled), "
        ".v-date-picker-table td button"
    )
    for btn in buttons:
        if btn.inner_text().strip() == target_dia:
            btn.click()
            page.wait_for_timeout(300)
            return True

    return False


def _buscar_sumario(page: Page, data_iso: str) -> str:
    """Seleciona a data no calendário, clica em Atualizar e retorna o HTML."""
    try:
        ok = _selecionar_data_calendario(page, data_iso)
        if not ok:
            print(f"[{_agora()}]   Aviso: nao foi possivel selecionar {data_iso} no calendario.")

        # Clica no botão Atualizar
        page.click(
            "button:has-text('ATUALIZAR'), button:has-text('Atualizar'), "
            "button:has-text('atualizar'), button:has-text('Pesquisar')",
            timeout=8000
        )

        try:
            page.wait_for_selector("table, [role='rowgroup']", timeout=15000)
        except PWTimeout:
            pass

        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except PWTimeout:
            pass

        return page.content()

    except Exception as e:
        print(f"[{_agora()}] Erro ao buscar sumario: {e}")
        return ""


# ─── Parsing ──────────────────────────────────────────────────────────────────

def parsear_sumario(html: str, mapa_setores: dict, data_iso: str,
                    filial_filtro: str = "") -> list:
    soup      = BeautifulSoup(html, "lxml")
    registros = []

    table = None
    for tbl in soup.find_all("table"):
        ths  = " ".join(th.get_text(strip=True) for th in tbl.find_all("th")).lower()
        tds  = " ".join(td.get_text(strip=True) for td in tbl.find_all("td")[:30]).lower()
        texto = ths + " " + tds
        if "embalad" in texto or "programado" in texto or "vte" in texto or "vtt" in texto:
            table = tbl
            break

    if not table:
        return []

    for row in table.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) < 5:
            continue

        cols = [td.get_text(separator=" ", strip=True) for td in tds]

        turno_raw = cols[0]
        turno     = _extrair_turno(turno_raw)

        result = _extrair_filial_linha(cols[1])
        if not result:
            continue
        filial, linha = result

        if filial_filtro and filial != filial_filtro.upper():
            continue

        produto = cols[2].strip() if len(cols) > 2 else None
        meta    = _to_int(cols[3]) if len(cols) > 3 else 0
        prod    = _to_int(cols[4]) if len(cols) > 4 else 0

        # cols[5] = eficiencia% — pula
        emb_ok      = _to_int(cols[6]) if len(cols) > 6 else prod
        falha_falsa = _to_int(cols[7]) if len(cols) > 7 else 0
        defeitos    = _to_int(cols[8]) if len(cols) > 8 else 0

        setor = mapa_setores.get(linha, "")

        registros.append({
            "id":               _gerar_id(data_iso, linha, turno, produto or ""),
            "data":             data_iso,
            "setor":            setor,
            "linha":            linha,
            "turno":            turno,
            "semana":           _calcular_semana(data_iso),
            "modelo":           produto,
            "familia":          None,
            "hora_inicio":      None,
            "hora_fim":         None,
            "intervalo":        None,
            "producao_real":    prod,
            "qtd_perda":        falha_falsa,
            "defeitos":         defeitos,
            "meta":             meta,
            "parada_seg":       None,
            "codigo_parada":    None,
            "descricao_parada": None,
            "observacao":       None,
        })

    return registros


# ─── Banco ───────────────────────────────────────────────────────────────────

def salvar_no_banco(registros: list) -> int:
    if not registros:
        return 0
    if not DATABASE_URL:
        print(f"[{_agora()}] Erro: DATABASE_URL nao configurada.")
        return 0

    salvos = 0
    erros  = 0
    try:
        with psycopg.connect(DATABASE_URL, sslmode="require") as conn:
            with conn.cursor() as cur:
                for r in registros:
                    try:
                        cur.execute("SAVEPOINT sp")
                        cur.execute("""
                            INSERT INTO producao_coletada (
                                id, data, setor, linha, turno, semana, modelo, familia,
                                hora_inicio, hora_fim, intervalo,
                                producao_real, qtd_perda, defeitos, meta,
                                parada_seg, codigo_parada, descricao_parada,
                                observacao, coletado_em, origem
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s,
                                %s, NOW(), 'mes'
                            )
                            ON CONFLICT (id) DO UPDATE SET
                                producao_real    = EXCLUDED.producao_real,
                                qtd_perda        = EXCLUDED.qtd_perda,
                                defeitos         = EXCLUDED.defeitos,
                                meta             = EXCLUDED.meta,
                                coletado_em      = NOW()
                        """, (
                            r["id"],          r["data"],        r["setor"],     r["linha"],
                            r["turno"],       r["semana"],      r["modelo"],    r["familia"],
                            r["hora_inicio"], r["hora_fim"],    r["intervalo"],
                            r["producao_real"], r["qtd_perda"], r["defeitos"],  r["meta"],
                            r["parada_seg"],  r["codigo_parada"], r["descricao_parada"],
                            r["observacao"],
                        ))
                        cur.execute("RELEASE SAVEPOINT sp")
                        salvos += 1
                    except Exception as row_err:
                        cur.execute("ROLLBACK TO SAVEPOINT sp")
                        erros += 1
                        if erros == 1:
                            print(f"[{_agora()}] Erro no registro id={r.get('id')} linha={r.get('linha')}: {row_err}")

    except Exception as e:
        print(f"[{_agora()}] Erro de conexao: {e}")
        return 0

    if erros:
        print(f"[{_agora()}] {erros} registro(s) com erro.")
    print(f"[{_agora()}] Banco: {salvos} registros salvos/atualizados.")
    return salvos


# ─── API direta ───────────────────────────────────────────────────────────────

def _chamar_api_relatorio(data_iso: str, filial_filtro: str,
                          mapa_setores: dict) -> list:
    data_fmt = datetime.strptime(data_iso, "%Y-%m-%d").strftime("%Y%m%d")
    payload  = {
        "procedure":  "indicadores.listagem_linhas",
        "parametros": {
            "dataInicial": f"{data_fmt} 00:00:00",
            "dataFinal":   f"{data_fmt} 23:59:59",
        },
    }
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Referer":      SUMARIO_URL,
    }
    resp = requests.post(API_RELATORIO, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()

    registros = []
    for r in resp.json():
        result = _extrair_filial_linha(r.get("Descricao", ""))
        if not result:
            continue
        filial, linha = result
        if filial_filtro and filial != filial_filtro.upper():
            continue

        turno  = _extrair_turno_api(r.get("Turno", ""))
        setor  = mapa_setores.get(linha, "")
        modelo = (r.get("CodProduto") or "").strip() or None

        registros.append({
            "id":               _gerar_id(data_iso, linha, turno, modelo or ""),
            "data":             data_iso,
            "setor":            setor,
            "linha":            linha,
            "turno":            turno,
            "semana":           _calcular_semana(data_iso),
            "modelo":           modelo,
            "familia":          None,
            "hora_inicio":      None,
            "hora_fim":         None,
            "intervalo":        None,
            "producao_real":    r.get("OK", 0),
            "qtd_perda":        r.get("FFALSA", 0),
            "defeitos":         r.get("NOK", 0),
            "meta":             r.get("Programado", 0),
            "parada_seg":       None,
            "codigo_parada":    None,
            "descricao_parada": None,
            "observacao":       None,
        })

    return registros


# ─── Coleta principal ─────────────────────────────────────────────────────────

def coletar_producao(data_inicial: str, data_final: str, filial: str = "",
                     headless: bool = True) -> list:
    mapa_setores = _carregar_mapa_setores()
    todos: list  = []

    dt_ini = datetime.strptime(data_inicial, "%Y-%m-%d").date()
    dt_fim = datetime.strptime(data_final,   "%Y-%m-%d").date()
    dt     = dt_ini

    while dt <= dt_fim:
        data_iso = str(dt)
        print(f"[{_agora()}] Coletando {data_iso}...", end=" ", flush=True)
        try:
            registros = _chamar_api_relatorio(data_iso, filial, mapa_setores)
            todos.extend(registros)
            print(f"{len(registros)} registros.")
        except Exception as e:
            print(f"Erro: {e}")
        dt += timedelta(days=1)

    return todos


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    print("=" * 50)
    print("  PCP Venttos - Coletor MES (Sumário Produção)")
    print("=" * 50)

    headless      = "--headed" not in args
    filial_filtro = args[args.index("--filial") + 1] if "--filial" in args else ""

    # ── SNIFF: intercepta chamadas de rede para descobrir API interna ──
    if "--sniff" in args:
        if not MES_USUARIO or not MES_SENHA:
            print("Erro: defina MES_USUARIO e MES_SENHA no .env.")
            sys.exit(1)

        data_alvo = args[args.index("--data") + 1] if "--data" in args else str(date.today())
        print(f"Modo sniff (browser visivel) — data: {data_alvo}")
        print("Interceptando todas as chamadas de rede...\n")

        chamadas: list[dict] = []

        def _capturar_resposta(response) -> None:
            url    = response.url
            method = response.request.method
            status = response.status
            ctype  = response.headers.get("content-type", "")
            skip   = (
                any(ext in url for ext in [".js", ".css", ".png", ".jpg", ".ico", ".woff", ".svg"])
                or "sourcemap" in url
            )
            if skip:
                return
            req_body    = response.request.post_data or ""
            req_headers = dict(response.request.headers)
            body = ""
            try:
                if "json" in ctype:
                    body = json.dumps(response.json(), ensure_ascii=False)[:800]
                elif "text" in ctype:
                    body = response.text()[:400]
            except Exception:
                pass
            chamadas.append({
                "method":      method,
                "url":         url,
                "status":      status,
                "ctype":       ctype,
                "req_body":    req_body,
                "req_headers": req_headers,
                "body":        body,
            })

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page    = browser.new_page()
            page.on("response", _capturar_resposta)

            if not _fazer_login(page):
                browser.close()
                sys.exit(1)

            if not _navegar_para_sumario(page):
                print("Nao foi possivel abrir o Sumario de Producao.")
                browser.close()
                sys.exit(1)

            chamadas.clear()
            print(f"[sniff] Selecionando {data_alvo} e clicando Atualizar...")
            _buscar_sumario(page, data_alvo)
            page.wait_for_timeout(3000)

            print(f"\n{'='*60}")
            print(f"  {len(chamadas)} chamadas de rede capturadas apos Atualizar")
            print(f"{'='*60}")
            for c in chamadas:
                print(f"\n  {c['method']} {c['status']}  {c['url']}")
                if c["ctype"]:
                    print(f"  Content-Type: {c['ctype']}")
                if c["body"]:
                    print(f"  Resposta: {c['body'][:400]}")

            json_calls = [c for c in chamadas if "json" in c["ctype"]]
            if json_calls:
                print(f"\n{'='*60}")
                print(f"  *** {len(json_calls)} chamada(s) JSON — CONTRATO COMPLETO DA API ***")
                print(f"{'='*60}")
                for c in json_calls:
                    print(f"\n  {c['method']} {c['url']}")
                    print(f"\n  REQUEST BODY:")
                    print(f"    {c['req_body']}")
                    hdrs_relevantes = {
                        k: v for k, v in c["req_headers"].items()
                        if k.lower() in ("content-type", "cookie", "authorization",
                                         "x-requested-with", "referer", "origin")
                    }
                    if hdrs_relevantes:
                        print(f"\n  HEADERS DA REQUISICAO:")
                        for k, v in hdrs_relevantes.items():
                            print(f"    {k}: {v[:200]}")
                    print(f"\n  RESPOSTA (primeiros 800 chars):")
                    print(f"    {c['body'][:800]}")
            else:
                print("\n  Nenhuma resposta JSON encontrada. O sistema pode usar SSR/HTML puro.")

            input("\n  Pressione Enter para fechar o browser...")
            browser.close()
        sys.exit(0)

    # ── DEBUG ──
    if "--debug" in args:
        if not MES_USUARIO or not MES_SENHA:
            print("Erro: defina MES_USUARIO e MES_SENHA no .env.")
            sys.exit(1)
        print("Modo debug (browser visivel)...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page    = browser.new_page()

            ok = _fazer_login(page)
            print(f"  URL apos login: {page.url}")

            if not ok:
                input("  Login falhou. Enter para fechar.")
                browser.close()
                sys.exit(1)

            print("\n  --- Textos visiveis no sidebar ---")
            textos = set()
            for el in page.query_selector_all("a, button, span, li, nav *"):
                try:
                    t = el.inner_text().strip()
                    if t and len(t) < 60:
                        textos.add(t)
                except Exception:
                    pass
            for t in sorted(textos):
                print(f"    '{t}'")
            print("  ---")

            print(f"\n  Navegando para Sumario de Producao ({SUMARIO_URL})...")
            ok_nav = _navegar_para_sumario(page)
            print(f"  URL apos navegacao: {page.url}")
            print(f"  Navegacao OK: {ok_nav}")

            print(f"\n  Inputs na pagina:")
            for inp in page.query_selector_all("input"):
                itype = inp.get_attribute("type") or "text"
                ph    = inp.get_attribute("placeholder") or ""
                val   = inp.get_attribute("value") or ""
                print(f"    type='{itype}' | placeholder='{ph}' | value='{val}'")

            print(f"\n  Botoes na pagina:")
            for btn in page.query_selector_all("button"):
                print(f"    '{btn.inner_text().strip()}'")

            # Testa abertura do calendário
            print(f"\n  Testando abertura do calendário...")
            inputs = page.query_selector_all("input[type='text'], input[type='date']")
            if inputs:
                inputs[0].click()
                try:
                    page.wait_for_selector(".v-date-picker-table, .v-picker__body", timeout=5000)
                    header = page.query_selector(
                        ".v-date-picker-header__value button, "
                        ".v-date-picker-header .v-btn:not(.v-btn--icon)"
                    )
                    print(f"  Calendario abriu! Header: '{header.inner_text().strip() if header else 'N/A'}'")
                    botoes_dia = page.query_selector_all(".v-date-picker-table button")
                    print(f"  Botoes de dia encontrados: {len(botoes_dia)}")
                    page.keyboard.press("Escape")
                except PWTimeout:
                    print("  Calendario nao abriu (timeout). O campo pode ser de tipo diferente.")
            else:
                print("  Nenhum input encontrado.")

            hoje = str(date.today())
            print(f"\n  Testando busca para {hoje}...")
            html = _buscar_sumario(page, hoje)
            registros = parsear_sumario(html, {}, hoje) if html else []
            print(f"  Registros parseados: {len(registros)}")
            for r in registros[:5]:
                print(f"    {r['linha']:20} | turno={r['turno']:10} | modelo={r.get('modelo','')[:25]:25} | meta={r['meta']:5} | prod={r['producao_real']:5}")
            if not registros and html:
                print("  Primeiros 1500 chars do HTML retornado:")
                print(html[:1500])

            input("\n  Pressione Enter para fechar o browser...")
            browser.close()
        sys.exit(0)

    # ── IMPORTAR ──
    if "--importar" in args:
        arquivo = args[args.index("--importar") + 1]
        print(f"  Lendo: {arquivo}")
        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
        print(f"  Registros: {len(dados)}")
        print(f"  Salvos: {salvar_no_banco(dados)}")
        sys.exit(0)

    # ── DATA ESPECIFICA ──
    if "--data" in args:
        data  = args[args.index("--data") + 1]
        dados = coletar_producao(data, data, filial_filtro, headless)
        print(f"  Buscados: {len(dados)} registros para {data}")
        if "--json" in args:
            _salvar_json(args[args.index("--json") + 1], dados)
        else:
            salvar_no_banco(dados)
        sys.exit(0)

    # ── INTERVALO ──
    if "--de" in args and "--ate" in args:
        de  = args[args.index("--de")  + 1]
        ate = args[args.index("--ate") + 1]
        dados = coletar_producao(de, ate, filial_filtro, headless)
        print(f"  Buscados: {len(dados)} registros de {de} a {ate}")
        if "--json" in args:
            _salvar_json(args[args.index("--json") + 1], dados)
        else:
            salvar_no_banco(dados)
        sys.exit(0)

    # ── PADRÃO: hoje ──
    hoje  = str(date.today())
    dados = coletar_producao(hoje, hoje, filial_filtro, headless)
    print(f"  Coletados hoje: {len(dados)} registros")
    salvar_no_banco(dados)
