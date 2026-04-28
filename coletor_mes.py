"""
PCP Venttos - Coletor MES
Faz scraping do Sistema MES e salva dados de producao no banco Railway.

Uso:
    python coletor_mes.py --data 2026-04-28
    python coletor_mes.py --de 2026-04-01 --ate 2026-04-28
    python coletor_mes.py --de 2026-04-01 --ate 2026-04-28 --filial VTE
    python coletor_mes.py --de 2026-04-01 --ate 2026-04-28 --json dados_mes.json
    python coletor_mes.py --importar dados_mes.json

Variaveis de ambiente (.env):
    DATABASE_URL  -> string de conexao PostgreSQL Railway
    MES_URL       -> URL base do sistema MES (padrao: http://192.168.1.32)
    MES_USUARIO   -> usuario de login
    MES_SENHA     -> senha de login
"""

import os
import sys
import json
import hashlib
import re
import requests
import psycopg
from bs4 import BeautifulSoup
from datetime import datetime, date

from dotenv import load_dotenv
load_dotenv()

MES_URL      = os.environ.get("MES_URL", "http://192.168.1.32")
MES_USUARIO  = os.environ.get("MES_USUARIO", "")
MES_SENHA    = os.environ.get("MES_SENHA", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

FILIAIS_VALIDAS = {"VTE", "VTT"}


def _agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _gerar_id(data: str, codigo_linha: str, turno_raw: str, hora_inicio: str, codigo_op: str) -> int:
    key = f"mes|{data}|{codigo_linha}|{turno_raw}|{hora_inicio}|{codigo_op}"
    digest = hashlib.md5(key.encode()).hexdigest()[:14]
    return int(digest, 16) + 10 ** 14


def _parsear_data_br(data_str: str) -> str:
    try:
        return datetime.strptime(data_str.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return ""


def _calcular_semana(data_iso: str) -> int | None:
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").isocalendar()[1]
    except Exception:
        return None


def _to_int(s: str) -> int:
    try:
        return int(float(s.replace(",", ".").strip()))
    except (ValueError, AttributeError):
        return 0


def _extrair_linha_info(option_text: str) -> dict | None:
    if "|" not in option_text:
        return None

    codigo, nome = option_text.split("|", 1)
    codigo = codigo.strip()
    nome   = nome.strip()

    if " - " in nome:
        filial, linha_nome = nome.split(" - ", 1)
        filial     = filial.strip()
        linha_nome = linha_nome.strip()
    else:
        matched = False
        for f in FILIAIS_VALIDAS:
            if nome.startswith(f + "-"):
                filial     = f
                linha_nome = nome[len(f) + 1:]
                matched    = True
                break
        if not matched:
            return None

    if filial not in FILIAIS_VALIDAS:
        return None

    return {"codigo": codigo, "filial": filial, "linha": linha_nome}


def _extrair_turno(turno_raw: str) -> str:
    parte = turno_raw.split("|", 1)[-1].strip() if "|" in turno_raw else turno_raw.strip()
    if parte.startswith("1T"):
        return "1º Turno"
    if parte.startswith("2T"):
        return "2º Turno"
    if parte.startswith("3T"):
        return "3º Turno"
    return parte


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


def fazer_login() -> requests.Session | None:
    session = requests.Session()
    login_url = f"{MES_URL}/authority/Account/Login"

    try:
        resp = session.get(login_url, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        form = soup.find("form")
        if not form:
            print(f"[{_agora()}] Formulario de login nao encontrado na pagina MES.")
            return None

        payload: dict[str, str] = {}
        for inp in form.find_all("input"):
            name = inp.get("name")
            if name:
                payload[name] = inp.get("value", "")

        user_field = None
        pass_field = None
        for inp in form.find_all("input"):
            itype = (inp.get("type") or "text").lower()
            iname = (inp.get("name") or "").lower()
            iid   = (inp.get("id")   or "").lower()
            if itype == "password":
                pass_field = inp.get("name")
            elif itype in ("text", "email") or any(k in iname + iid for k in ("user", "login", "email", "nome")):
                if not user_field:
                    user_field = inp.get("name")

        if user_field:
            payload[user_field] = MES_USUARIO
        if pass_field:
            payload[pass_field] = MES_SENHA

        resp = session.post(login_url, data=payload, timeout=15, allow_redirects=True)

        if "/Account/Login" in resp.url:
            print(f"[{_agora()}] Falha no login MES: verifique MES_USUARIO e MES_SENHA no .env.")
            return None

        print(f"[{_agora()}] Login MES OK.")
        return session

    except requests.exceptions.ConnectionError:
        print(f"[{_agora()}] Erro: nao foi possivel conectar ao MES em {MES_URL}. Verifique a rede.")
        return None
    except Exception as e:
        print(f"[{_agora()}] Erro no login MES: {e}")
        return None


def obter_linhas_disponiveis(session: requests.Session) -> list:
    try:
        resp = session.get(f"{MES_URL}/sfc/HoraRelatorio", timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        select = soup.find("select")
        if not select:
            print(f"[{_agora()}] Select de linhas nao encontrado na pagina do relatorio MES.")
            return []

        linhas = []
        for option in select.find_all("option"):
            text  = option.get_text(strip=True)
            value = option.get("value", "").strip()
            if not value:
                continue
            info = _extrair_linha_info(text)
            if info:
                info["value"] = value
                linhas.append(info)

        print(f"[{_agora()}] {len(linhas)} linhas VTE/VTT disponiveis no MES.")
        return linhas

    except Exception as e:
        print(f"[{_agora()}] Erro ao obter linhas do MES: {e}")
        return []


def buscar_relatorio(session: requests.Session, linha_value: str,
                     data_ini: str, data_fim: str) -> str | None:
    url = f"{MES_URL}/sfc/HoraRelatorio"
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        form = soup.find("form")
        campo_linha    = "Linha"
        campo_data_ini = "DataInicio"
        campo_data_fim = "DataFim"

        payload: dict[str, str] = {}

        if form:
            for inp in form.find_all("input", {"type": "hidden"}):
                name = inp.get("name")
                if name:
                    payload[name] = inp.get("value", "")

            select = form.find("select")
            if select and select.get("name"):
                campo_linha = select.get("name")

            date_inputs = []
            for inp in form.find_all("input"):
                itype = (inp.get("type") or "").lower()
                iname = (inp.get("name") or "").lower()
                if itype == "hidden":
                    continue
                if itype == "date" or any(k in iname for k in ("data", "date", "inicio", "fim", "start", "end")):
                    date_inputs.append(inp)

            if len(date_inputs) >= 1:
                campo_data_ini = date_inputs[0].get("name", campo_data_ini)
            if len(date_inputs) >= 2:
                campo_data_fim = date_inputs[1].get("name", campo_data_fim)

        dt_ini = datetime.strptime(data_ini, "%Y-%m-%d").strftime("%d/%m/%Y")
        dt_fim = datetime.strptime(data_fim, "%Y-%m-%d").strftime("%d/%m/%Y")

        payload[campo_linha]    = linha_value
        payload[campo_data_ini] = dt_ini
        payload[campo_data_fim] = dt_fim

        resp = session.post(url, data=payload, timeout=30)
        resp.raise_for_status()
        return resp.text

    except Exception as e:
        print(f"[{_agora()}] Erro ao buscar relatorio (linha_value={linha_value}): {e}")
        return None


def parsear_resultado(html: str, info_linha: dict, mapa_setores: dict) -> list:
    soup = BeautifulSoup(html, "lxml")
    registros = []
    setor = mapa_setores.get(info_linha["linha"], "")

    tables = []
    for tbl in soup.find_all("table"):
        th_texts = {th.get_text(strip=True) for th in tbl.find_all("th")}
        if "Programado" in th_texts or "Boas produzidas" in th_texts:
            tables.append(tbl)

    if not tables:
        return []

    full_text = soup.get_text(separator="\n")

    header_re  = re.compile(r'(\d{2}/\d{2}/\d{4})\s*[-–]\s*Turno:\s*(\S+)')
    ordem_re   = re.compile(r'Ordem\s+de\s+produ[cç][aã]o:\s*(\S+)', re.IGNORECASE)
    produto_re = re.compile(r'Produto:\s*(\S+)', re.IGNORECASE)

    headers_found = list(header_re.finditer(full_text))
    ordens        = [m.group(1) for m in ordem_re.finditer(full_text)]
    produtos      = [m.group(1) for m in produto_re.finditer(full_text)]

    for i, table in enumerate(tables):
        header    = headers_found[i] if i < len(headers_found) else None
        data_iso  = _parsear_data_br(header.group(1)) if header else None
        turno_raw = header.group(2) if header else ""
        turno     = _extrair_turno(turno_raw)
        codigo_op = ordens[i]  if i < len(ordens)   else None
        produto   = produtos[i] if i < len(produtos) else None

        for row in table.find_all("tr"):
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cols) < 5:
                continue

            hora_match = re.match(r"(\d{2}:\d{2})\s*[-–]\s*(\d{2}:\d{2})", cols[1])
            if not hora_match:
                continue

            hora_inicio = hora_match.group(1)
            hora_fim    = hora_match.group(2)

            registros.append({
                "id":               _gerar_id(data_iso or "", info_linha["codigo"], turno_raw, hora_inicio, codigo_op or ""),
                "data":             data_iso or None,
                "setor":            setor,
                "linha":            info_linha["linha"],
                "turno":            turno,
                "semana":           _calcular_semana(data_iso) if data_iso else None,
                "modelo":           produto,
                "familia":          None,
                "hora_inicio":      hora_inicio,
                "hora_fim":         hora_fim,
                "intervalo":        cols[1],
                "producao_real":    _to_int(cols[2]),
                "qtd_perda":        _to_int(cols[3]),
                "defeitos":         _to_int(cols[4]),
                "meta":             _to_int(cols[0]),
                "parada_seg":       None,
                "codigo_parada":    None,
                "descricao_parada": None,
                "observacao":       codigo_op or None,
            })

    return registros


def coletar_producao(data_inicial: str, data_final: str, filial: str = "") -> list:
    if not MES_USUARIO or not MES_SENHA:
        print(f"[{_agora()}] Erro: defina MES_USUARIO e MES_SENHA no arquivo .env.")
        return []

    session = fazer_login()
    if not session:
        return []

    linhas = obter_linhas_disponiveis(session)
    if not linhas:
        return []

    if filial:
        linhas = [l for l in linhas if l["filial"] == filial.upper()]
        print(f"[{_agora()}] Filtrando: {len(linhas)} linhas da filial {filial.upper()}.")

    mapa_setores = _carregar_mapa_setores()
    todos: list = []

    for info in linhas:
        label = f"{info['filial']} - {info['linha']}"
        print(f"[{_agora()}] Coletando {label}...", end=" ", flush=True)
        html = buscar_relatorio(session, info["value"], data_inicial, data_final)
        if not html:
            print("sem resposta.")
            continue
        registros = parsear_resultado(html, info, mapa_setores)
        todos.extend(registros)
        print(f"{len(registros)} registros.")

    return todos


def salvar_no_banco(registros: list) -> int:
    if not registros:
        return 0
    if not DATABASE_URL:
        print(f"[{_agora()}] Erro: DATABASE_URL nao configurada.")
        return 0

    salvos = 0
    try:
        with psycopg.connect(DATABASE_URL, sslmode="require") as conn:
            with conn.cursor() as cur:
                for r in registros:
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
                            observacao       = EXCLUDED.observacao,
                            coletado_em      = NOW()
                    """, (
                        r["id"],          r["data"],        r["setor"],     r["linha"],
                        r["turno"],       r["semana"],      r["modelo"],    r["familia"],
                        r["hora_inicio"], r["hora_fim"],    r["intervalo"],
                        r["producao_real"], r["qtd_perda"], r["defeitos"],  r["meta"],
                        r["parada_seg"],  r["codigo_parada"], r["descricao_parada"],
                        r["observacao"],
                    ))
                    salvos += 1

        print(f"[{_agora()}] Banco: {salvos} registros salvos/atualizados.")
        return salvos

    except Exception as e:
        print(f"[{_agora()}] Erro ao salvar no banco: {e}")
        return 0


if __name__ == "__main__":
    args = sys.argv[1:]

    print("=" * 50)
    print("  PCP Venttos - Coletor MES")
    print("=" * 50)

    filial_filtro = ""
    if "--filial" in args:
        filial_filtro = args[args.index("--filial") + 1]

    if "--importar" in args:
        arquivo = args[args.index("--importar") + 1]
        print(f"  Lendo: {arquivo}")
        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
        print(f"  Registros: {len(dados)}")
        print(f"  Salvos: {salvar_no_banco(dados)}")
        sys.exit(0)

    if "--data" in args:
        data  = args[args.index("--data") + 1]
        dados = coletar_producao(data, data, filial_filtro)
        print(f"  Buscados: {len(dados)} registros para {data}")
        if "--json" in args:
            arquivo = args[args.index("--json") + 1]
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, default=str)
            print(f"  Salvo em: {arquivo}")
        else:
            print(f"  Salvos: {salvar_no_banco(dados)}")
        sys.exit(0)

    if "--de" in args and "--ate" in args:
        de  = args[args.index("--de")  + 1]
        ate = args[args.index("--ate") + 1]
        dados = coletar_producao(de, ate, filial_filtro)
        print(f"  Buscados: {len(dados)} registros de {de} a {ate}")
        if "--json" in args:
            arquivo = args[args.index("--json") + 1]
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, default=str)
            print(f"  Salvo em: {arquivo}")
        else:
            print(f"  Salvos: {salvar_no_banco(dados)}")
        sys.exit(0)

    hoje  = str(date.today())
    dados = coletar_producao(hoje, hoje, filial_filtro)
    print(f"  Coletados hoje: {len(dados)} registros")
    salvar_no_banco(dados)
