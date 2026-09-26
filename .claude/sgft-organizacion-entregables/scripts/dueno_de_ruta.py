#!/usr/bin/env python3
"""
dueno_de_ruta.py — Consulta el mapa de propiedad del repositorio SGFT.

Fuente única de verdad: assets/ownership.json (junto a este script, en ../assets/).

Uso:
  python scripts/dueno_de_ruta.py RUTA [RUTA ...]   Dueño, colaboradores, revisor y WBS de cada ruta
  python scripts/dueno_de_ruta.py --persona jesus    Todo lo que le toca a una persona
  python scripts/dueno_de_ruta.py --wbs 3.4.6        Rutas y personas ligadas a un paquete WBS
  python scripts/dueno_de_ruta.py --codeowners       Imprime el contenido de .github/CODEOWNERS
  python scripts/dueno_de_ruta.py --codeowners --salida RUTA/.github/CODEOWNERS
                                                     Lo escribe en UTF-8 (usar esto en Windows/PowerShell,
                                                     donde ">" guarda en UTF-16 y GitHub no lo lee)
  python scripts/dueno_de_ruta.py --verificar        Autoprueba de consistencia del mapa
  git diff --name-only origin/main...HEAD | python scripts/dueno_de_ruta.py --revisar
                                                     Revisión de rutas de un PR (integrador): tabla de
                                                     dueños y aprobadores; termina con código 1 si algún
                                                     archivo está fuera de la estructura o en evaluación

Resolución: cuando varias reglas coinciden, gana la de mayor "prioridad" (campo opcional,
0 por omisión; vale 1 en las reglas transversales de datos: models.py, migrations/, fixtures/);
a igual prioridad, la más específica (más caracteres literales, sin contar comodines);
a igual especificidad, la que aparece después en el JSON.
CODEOWNERS se genera ordenado de menos a más específico, de modo que la semántica
"gana la última coincidencia" de GitHub produce exactamente el mismo resultado.
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ_SKILL = Path(__file__).resolve().parent.parent
MAPA = RAIZ_SKILL / "assets" / "ownership.json"


# ---------------------------------------------------------------- carga y coincidencia

def cargar_mapa(ruta=MAPA):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def patron_a_regex(patron):
    """Glob estilo gitignore/CODEOWNERS: ** cruza carpetas, * y ? no cruzan '/'."""
    salida, i = [], 0
    while i < len(patron):
        if patron.startswith("**", i):
            salida.append(".*")
            i += 2
        elif patron[i] == "*":
            salida.append("[^/]*")
            i += 1
        elif patron[i] == "?":
            salida.append("[^/]")
            i += 1
        else:
            salida.append(re.escape(patron[i]))
            i += 1
    return re.compile("^" + "".join(salida) + "$")


def especificidad(patron):
    return len(patron.replace("*", "").replace("?", ""))


def clave_orden(idx, regla):
    return (regla.get("prioridad", 0), especificidad(regla["patron"]), idx)


def normalizar(ruta):
    ruta = ruta.strip().replace("\\", "/")
    for prefijo in ("./", "/"):
        while ruta.startswith(prefijo):
            ruta = ruta[len(prefijo):]
    if ruta.startswith("sgft/"):  # nombre de la carpeta raíz en estructura-y-flujo §1
        ruta = ruta[len("sgft/"):]
    return ruta


def resolver(ruta, mapa):
    ruta = normalizar(ruta)
    candidatas = [
        (clave_orden(idx, r), r)
        for idx, r in enumerate(mapa["reglas"])
        if patron_a_regex(r["patron"]).match(ruta)
    ]
    if not candidatas:
        return None
    candidatas.sort(key=lambda t: t[0])
    return candidatas[-1][1]


def aprobadores(regla, mapa):
    """Quienes pueden aprobar un PR sobre la ruta: dueño, colaboradores, revisores y el
    aprobador general (DEC-18), sin duplicados y en ese orden."""
    claves = [regla["dueno"]] + regla.get("colaboradores", []) + regla.get("revisor", [])
    general = mapa.get("aprobador_general")
    if general:
        claves.append(general)
    vistos = []
    for c in claves:
        if c not in vistos:
            vistos.append(c)
    return vistos


# ---------------------------------------------------------------- presentación

def nombre(clave, mapa):
    persona = mapa["integrantes"].get(clave)
    return f"{persona['nombre']} ({persona['capa']})" if persona else clave


def lista(claves, mapa):
    return ", ".join(nombre(c, mapa) for c in claves) if claves else "—"


def imprimir_ruta(ruta, mapa):
    regla = resolver(ruta, mapa)
    print(f"\nRuta: {normalizar(ruta)}")
    if regla is None or regla["patron"] == "**":
        print("  ⚠ Fuera de la estructura aprobada. No crear el archivo: pedir ubicación y dueño al integrador (Tarín).")
        return
    print(f"  Regla aplicada   : {regla['patron']}")
    print(f"  Dueño            : {nombre(regla['dueno'], mapa)}")
    print(f"  Colaboradores    : {lista(regla.get('colaboradores', []), mapa)}")
    print(f"  Revisor          : {lista(regla.get('revisor', []), mapa)}")
    if mapa.get("aprobador_general"):
        print(f"  Aprobador general: {nombre(mapa['aprobador_general'], mapa)} — su aprobación basta (DEC-18)")
    print(f"  Paquetes WBS     : {', '.join(regla.get('wbs', [])) or '—'}")
    if regla.get("en_evaluacion"):
        print("  ⏸ EN EVALUACIÓN : paquete fuera de la línea base; NO crear el archivo hasta que el equipo lo apruebe")
    if regla.get("pareja_obligatoria"):
        print("  Pareja           : OBLIGATORIA (ADR-02 §6) — ningún archivo con un solo autor")
    for f in regla.get("funciones_con_otro_autor", []):
        print(f"  Función ajena    : {f['funcion']} → autor {f['autor']} (WBS {f['wbs']}). {f['motivo']}")
    print(f"  Nota             : {regla.get('nota', '')}")


def imprimir_persona(clave, mapa):
    if clave not in mapa["integrantes"]:
        sys.exit(f"Persona desconocida: {clave}. Opciones: {', '.join(mapa['integrantes'])}")
    print(f"\n{nombre(clave, mapa)} — {mapa['integrantes'][clave]['rol_scrum']}")
    if mapa.get("aprobador_general") == clave:
        print("  Aprobador general: puede aprobar un PR sobre cualquier ruta (DEC-18).")
    secciones = {"Dueño de": [], "Colabora / pareja en": [], "Revisor obligatorio de": [], "Escribe funciones en archivos ajenos": []}
    for r in mapa["reglas"]:
        if r["patron"] == "**":
            continue
        wbs = f"  [WBS {', '.join(r.get('wbs', []))}]" if r.get("wbs") else ""
        if r["dueno"] == clave:
            secciones["Dueño de"].append(f"{r['patron']}{wbs}")
        if clave in r.get("colaboradores", []):
            secciones["Colabora / pareja en"].append(f"{r['patron']}{wbs}")
        if clave in r.get("revisor", []):
            secciones["Revisor obligatorio de"].append(f"{r['patron']}{wbs}")
        for f in r.get("funciones_con_otro_autor", []):
            if clave in f["autor"]:
                secciones["Escribe funciones en archivos ajenos"].append(f"{r['patron']} → {f['funcion']} [WBS {f['wbs']}]")
    for titulo, filas in secciones.items():
        print(f"\n  {titulo}:")
        for fila in filas or ["—"]:
            print(f"    • {fila}")


def imprimir_wbs(codigo, mapa):
    print(f"\nPaquete WBS {codigo}")
    if codigo in mapa.get("paquetes_en_evaluacion", {}):
        print(f"  ⏸ EN EVALUACIÓN: {mapa['paquetes_en_evaluacion'][codigo]}")
    hallado = False
    for r in mapa["reglas"]:
        directo = codigo in r.get("wbs", [])
        funciones = [f for f in r.get("funciones_con_otro_autor", []) if codigo in f["wbs"]]
        if directo or funciones:
            hallado = True
            print(f"  • {r['patron']}: dueño {nombre(r['dueno'], mapa)}"
                  + (f"; colaboran {lista(r.get('colaboradores', []), mapa)}" if r.get("colaboradores") else "")
                  + (f"; revisa {lista(r.get('revisor', []), mapa)}" if r.get("revisor") else ""))
            for f in funciones:
                print(f"      ↳ {f['funcion']} → {f['autor']}")
    if not hallado:
        print("  Sin rutas registradas. Revisar references/matriz-wbs-responsables.md (puede ser un entregable fuera del repositorio).")


def generar_codeowners(mapa):
    lineas = [
        "# CODEOWNERS — SGFT",
        "# GENERADO con: python scripts/dueno_de_ruta.py --codeowners",
        "# No editar a mano: modificar assets/ownership.json de la skill y regenerar.",
        "# Los usuarios de GitHub se definen en assets/ownership.json (campo \"github\" de cada integrante).",
        "# Si ves @TODO_<nombre>, complétalo AHÍ y regenera; si lo editas aquí, la próxima generación lo borra.",
        "# GitHub aplica la ÚLTIMA regla que coincide; las reglas están ordenadas de general a específica.",
        "# main protegido con dos rulesets (DEC-16). El integrador (Tarín) figura en TODAS las rutas:",
        "# su aprobación basta para cualquier archivo y es el único que fusiona (DEC-18). Sus propios",
        "# PR los aprueba otro de los listados, porque GitHub no deja aprobar el PR propio.",
        "# Cada ruta lista además al menos otra persona, para que los PR del integrador puedan aprobarse.",
        "",
    ]
    ordenadas = sorted(enumerate(mapa["reglas"]), key=lambda t: clave_orden(*t))
    for _, r in ordenadas:
        cuentas = " ".join(mapa["integrantes"][c]["github"] for c in aprobadores(r, mapa))
        patron = "*" if r["patron"] == "**" else "/" + r["patron"]
        lineas.append(f"{patron:<52} {cuentas}")
    return "\n".join(lineas) + "\n"


# ---------------------------------------------------------------- revisión de un PR (integrador)

def revisar(rutas, mapa):
    """Tabla de rutas de un PR. Devuelve 1 si alguna está fuera de la estructura o en evaluación."""
    rutas = [normalizar(r) for r in rutas if r.strip()]
    if not rutas:
        print("Sin rutas que revisar.")
        return 0
    bloqueos, avisos = [], []
    ancho = min(max(len(r) for r in rutas), 60)
    print(f"\n{'Ruta':<{ancho}}  {'Dueño':<7} {'Pueden aprobar':<50} Estado")
    print("-" * (ancho + 78))
    for ruta in rutas:
        r = resolver(ruta, mapa)
        if r is None or r["patron"] == "**":
            dueno, aprueban, estado = "—", "(el integrador decide)", "✗ FUERA DE LA ESTRUCTURA"
            bloqueos.append(ruta)
        else:
            dueno = r["dueno"]
            aprueban = " ".join(mapa["integrantes"][c]["github"] for c in aprobadores(r, mapa))
            if r.get("en_evaluacion"):
                estado = "✗ PAQUETE EN EVALUACIÓN"
                bloqueos.append(ruta)
            elif r.get("pareja_obligatoria"):
                estado = "⚠ pareja obligatoria"
                avisos.append(ruta)
            elif r.get("funciones_con_otro_autor"):
                estado = "⚠ tiene funciones de otro autor"
                avisos.append(ruta)
            else:
                estado = "OK"
        print(f"{ruta:<{ancho}}  {dueno:<7} {aprueban:<50} {estado}")
    print()
    if avisos:
        print(f"⚠ {len(avisos)} ruta(s) con aviso: confirma la coautoría (Co-authored-by) o que el autor de la función ajena revisó.")
    if bloqueos:
        print(f"✗ {len(bloqueos)} ruta(s) bloquean la fusión: ubícalas en assets/ownership.json o espera la aprobación del paquete.")
        return 1
    print("✓ Todas las rutas están en la estructura aprobada.")
    return 0


# ---------------------------------------------------------------- autoprueba

CASOS_ESPERADOS = [
    ("apps/pos/models.py", "jesus"),
    ("apps/__init__.py", "jesus"),
    ("apps/inventory/models.py", "jesus"),
    ("apps/accounts/models.py", "jesus"),
    ("apps/catalog/models.py", "jesus"),
    ("apps/inventory/fixtures/stock_demo.json", "yahir"),
    ("apps/inventory/migrations/0001_initial.py", "jesus"),
    ("apps/inventory/migrations/0002_stockmovement.py", "jesus"),
    ("apps/pos/views.py", "jared"),
    ("apps/pos/urls.py", "jared"),
    ("apps/pos/services.py", "jesus"),
    ("apps/pos/services_pricing.py", "jesus"),
    ("apps/pos/templates/pos/partials/dish_list.html", "tarin"),
    ("apps/pos/templates/pos/partials/cash_session_banner.html", "tarin"),
    ("apps/accounts/views.py", "diego"),
    ("apps/accounts/templates/accounts/login.html", "yahir"),
    ("apps/catalog/admin.py", "diego"),
    ("apps/inventory/services.py", "diego"),
    ("apps/inventory/templates/inventory/partials/stock_alert_badge.html", "yahir"),
    ("apps/reports/services.py", "jared"),
    ("apps/reports/templates/reports/cash_close.html", "yahir"),
    ("apps/core/mixins.py", "jesus"),
    ("apps/core/templates/base.html", "tarin"),
    ("apps/catalog/fixtures/demo_menu.json", "yahir"),
    ("static/pos/sw.js", "tarin"),
    ("static/pos/db.js", "tarin"),
    ("tests_fixtures/pricing_cases.json", "jesus"),
    ("tests_e2e/parity/test_pricing.mjs", "tarin"),
    ("tests_e2e/test_cash_close.py", "yahir"),
    ("config/settings.py", "jesus"),
    (".github/workflows/ci.yml", "jared"),
    ("docs/SRS.md", "diego"),
    ("docs/diagramas/A0.drawio", "jesus"),
    ("docs/prototipos/rep-caja/index.html", "yahir"),
    ("docs/calidad/checklist-seguridad.md", "jesus"),
    ("docs/calidad/cobertura-sprint-3.md", "jared"),
    ("sgft/apps/pos/models.py", "jesus"),
    ("apps/pos/templates/pos/review/quarantine_list.html", "yahir"),
    ("apps/pos/templates/pos/cash_session_close.html", "yahir"),
    ("apps/pos/templates/pos/kitchen_queue.html", "tarin"),
    ("apps/pos/templates/pos/partials/kitchen_order.html", "tarin"),
    ("static/pos/app.css", "tarin"),
    ("docs/decisiones/contrato-sync-pdv.md", "jesus"),
    ("docs/decisiones/nombres-modulo-precios.md", "jesus"),
    ("docs/decisiones/organizacion-repositorio.md", "tarin"),
    ("docs/decisiones/ADR-02-operacion-offline-SGFT.md", "diego"),
    ("README.md", "tarin"),
    (".github/CODEOWNERS", "tarin"),
    (".claude/skills/sgft-organizacion-entregables/SKILL.md", "tarin"),
]


def ultima_coincidencia_codeowners(ruta, mapa):
    ordenadas = sorted(enumerate(mapa["reglas"]), key=lambda t: clave_orden(*t))
    ganadora = None
    for _, r in ordenadas:
        if patron_a_regex(r["patron"]).match(normalizar(ruta)):
            ganadora = r
    return ganadora


def verificar(mapa):
    errores = []
    claves = set(mapa["integrantes"])
    if mapa.get("aprobador_general") and mapa["aprobador_general"] not in claves:
        errores.append(f"aprobador_general desconocido: {mapa['aprobador_general']}")
    patrones = set()
    for r in mapa["reglas"]:
        if r["patron"] in patrones:
            errores.append(f"Patrón duplicado: {r['patron']}")
        patrones.add(r["patron"])
        for campo in ("colaboradores", "revisor"):
            for c in [r["dueno"]] + r.get(campo, []):
                if c not in claves:
                    errores.append(f"{r['patron']}: persona desconocida '{c}'")
        personas = {r["dueno"], *r.get("colaboradores", []), *r.get("revisor", [])}
        if len(personas) < 2:
            errores.append(f"{r['patron']}: solo una persona; con revisión obligatoria bloquearía sus propios PR")
        if r["dueno"] in r.get("revisor", []):
            errores.append(f"{r['patron']}: el dueño no puede ser su propio revisor")
        if r.get("pareja_obligatoria") and not r.get("colaboradores"):
            errores.append(f"{r['patron']}: pareja obligatoria sin colaborador")
        for w in r.get("wbs", []):
            if not re.fullmatch(r"\d(\.\d){1,2}", w):
                errores.append(f"{r['patron']}: código WBS inválido '{w}'")
    for ruta, esperado in CASOS_ESPERADOS:
        obtenido = resolver(ruta, mapa)["dueno"]
        if obtenido != esperado:
            errores.append(f"{ruta}: se esperaba {esperado}, se obtuvo {obtenido}")
        if ultima_coincidencia_codeowners(ruta, mapa)["dueno"] != obtenido:
            errores.append(f"{ruta}: CODEOWNERS y el script no coinciden")
    if errores:
        print("✗ Mapa inconsistente:")
        for e in errores:
            print("  -", e)
        return 1
    print(f"✓ Mapa consistente: {len(mapa['reglas'])} reglas, {len(CASOS_ESPERADOS)} casos verificados, CODEOWNERS equivalente.")
    return 0


# ---------------------------------------------------------------- CLI

def main():
    p = argparse.ArgumentParser(description="Mapa de propiedad del repositorio SGFT")
    p.add_argument("rutas", nargs="*")
    p.add_argument("--persona")
    p.add_argument("--wbs")
    p.add_argument("--codeowners", action="store_true")
    p.add_argument("--salida", help="con --codeowners: escribe el archivo en esta ruta (UTF-8) en vez de imprimirlo")
    p.add_argument("--verificar", action="store_true")
    p.add_argument("--revisar", action="store_true", help="revisa las rutas de un PR (como argumentos o una por línea en la entrada estándar)")
    p.add_argument("--mapa", default=str(MAPA))
    a = p.parse_args()
    mapa = cargar_mapa(a.mapa)

    if a.verificar:
        sys.exit(verificar(mapa))
    if a.revisar:
        rutas = a.rutas if a.rutas else sys.stdin.read().splitlines()
        sys.exit(revisar(rutas, mapa))
    if a.codeowners:
        contenido = generar_codeowners(mapa)
        if a.salida:
            destino = Path(a.salida)
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(contenido, encoding="utf-8", newline="\n")
            pendientes = sorted(c for c, p in mapa["integrantes"].items() if p["github"].startswith("@TODO_"))
            print(f"✓ CODEOWNERS escrito en {destino}")
            if pendientes:
                print(f"  ⚠ Falta el usuario de GitHub de: {', '.join(pendientes)} — defínelo en assets/ownership.json (campo github) y regenera.")
        else:
            sys.stdout.write(contenido)
        return
    if a.persona:
        clave = unicodedata.normalize("NFKD", a.persona).encode("ascii", "ignore").decode().lower().split()[0]
        imprimir_persona(clave, mapa)
    if a.wbs:
        imprimir_wbs(a.wbs, mapa)
    for ruta in a.rutas:
        imprimir_ruta(ruta, mapa)
    if not (a.persona or a.wbs or a.rutas):
        p.print_help()


if __name__ == "__main__":
    main()
