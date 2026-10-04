#!/usr/bin/env python3
"""Herramientas del sistema de diseño PuntoVenta (SGFT).

Fuente de verdad: assets/tokens.json (levantado de Figma).

Uso:
  python scripts/tokens.py contraste                 # evalúa todos los pares declarados (AA)
  python scripts/tokens.py contraste "#7A695D" "#FDF8F2"   # evalúa un par cualquiera
  python scripts/tokens.py buscar "#EF7125"          # token más cercano a un color suelto
  python scripts/tokens.py css [--salida ruta.css]   # genera las variables CSS (+ tema de Tailwind v4)
  python scripts/tokens.py verificar [--css ruta.css]  # valida tokens.json y, opcional, un CSS implementado

Sale con código 1 si 'verificar' encuentra errores (útil en CI).
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TOKENS = RAIZ / "assets" / "tokens.json"
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def cargar():
    with open(TOKENS, encoding="utf-8") as f:
        return json.load(f)


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminancia(h):
    def canal(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (canal(c) for c in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    la, lb = luminancia(a), luminancia(b)
    alto, bajo = max(la, lb), min(la, lb)
    return (alto + 0.05) / (bajo + 0.05)


def cmd_contraste(args):
    if len(args) == 2:
        c = contraste(args[0], args[1])
        print(f"{args[0]} sobre {args[1]}: {c:.2f}:1  "
              f"AA texto normal {'✔' if c >= 4.5 else '✘'} · AA texto grande {'✔' if c >= 3 else '✘'}")
        return 0
    datos = cargar()
    fallas = 0
    print(f"{'Par':62} {'Ratio':>7}  Mín  Resultado")
    for p in datos["pares_de_contraste"]:
        c = contraste(p["texto"], p["fondo"])
        ok = c >= p["minimo"]
        fallas += 0 if ok else 1
        print(f"{p['nombre']:62} {c:6.2f}:1 {p['minimo']:>4}  {'✔ cumple' if ok else '✘ NO cumple'}")
    print(f"\n{fallas} par(es) por debajo del mínimo. Ver references/auditoria-y-deuda.md §2 para las propuestas.")
    return 0


def cmd_buscar(args):
    if not args or not HEX.match(args[0]):
        print("Uso: tokens.py buscar \"#RRGGBB\"")
        return 1
    objetivo = rgb(args[0])
    datos = cargar()
    candidatos = []
    for grupo in ("color", "no_tokenizado"):
        for nombre, t in datos[grupo].items():
            v = t.get("valor")
            if v and HEX.match(v):
                d = sum((a - b) ** 2 for a, b in zip(objetivo, rgb(v))) ** 0.5
                candidatos.append((d, grupo, nombre, v))
    candidatos.sort()
    for d, grupo, nombre, v in candidatos[:5]:
        etiqueta = "variable Figma" if grupo == "color" else "valor documentado sin variable"
        print(f"{nombre:26} {v}  distancia {d:6.1f}  ({etiqueta})")
    if candidatos and candidatos[0][0] > 12:
        print("\nNingún token está cerca: no inventes el color; propón un token nuevo (references/auditoria-y-deuda.md §5).")
    return 0


def valor_css(t):
    """#RRGGBB, o rgba() si el token declara 'alfa'."""
    if "alfa" in t:
        r, g, b = rgb(t["valor"])
        return f"rgba({r}, {g}, {b}, {t['alfa']})"
    return t["valor"]


def generar_css():
    d = cargar()
    p = d["$meta"]["prefijo_css"]
    L = ["/* Generado por scripts/tokens.py css desde assets/tokens.json — no editar a mano. */",
         "/* Sistema de diseño PuntoVenta · El Pardo · SGFT */", ":root {"]
    L.append("  /* Color (variables Figma 'SGFT · Tokens', modo Claro) */")
    for n, t in d["color"].items():
        L.append(f"  {p}color-{slug(n)}: {valor_css(t)};")
    L.append("  /* Color documentado sin variable en Figma */")
    for n, t in d["no_tokenizado"].items():
        L.append(f"  {p}{slug(n)}: {valor_css(t)};")
    L.append("  /* Medidas (variables Figma 'SGFT · Medidas') */")
    for n, t in d["medida"].items():
        L.append(f"  {p}{slug(n)}: {t['valor']}px;")
    L.append("  /* Sombras (estilos de efecto) */")
    for n, t in d["sombra"].items():
        L.append(f"  {p}{slug(n)}: {t['css']};")
    L.append("  /* Gradientes */")
    for n, t in d["gradiente"].items():
        if "css" in t:
            L.append(f"  {p}gradiente-{slug(n)}: {t['css']};")
    fam = d["tipografia"]["familia"]
    L.append(f"  {p}fuente: '{fam}', system-ui, -apple-system, 'Segoe UI', sans-serif;")
    L.append("}")
    L.append("")
    # Tailwind v4 lee este bloque al compilar (input.css importa este archivo); el navegador nunca lo ve.
    # 'inline' hace que la utilidad use var(--sgft-…) en lugar de copiar el valor.
    L.append("/* Tema de Tailwind v4: bg-marca-primario, text-texto-secundario, rounded-md, p-lg, shadow-tarjeta… */")
    L.append("@theme inline {")
    L.append("  --color-*: initial;  /* sin la paleta de Tailwind: solo existen los colores del sistema */")
    for n in d["color"]:
        L.append(f"  --color-{slug(n)}: var({p}color-{slug(n)});")
    for n in d["no_tokenizado"]:
        L.append(f"  --color-{slug(n)}: var({p}{slug(n)});")
    for n in d["medida"]:
        s = slug(n)
        if s.startswith("radio-"):
            L.append(f"  --radius-{s[len('radio-'):]}: var({p}{s});")
        elif s.startswith("espacio-"):
            L.append(f"  --spacing-{s[len('espacio-'):]}: var({p}{s});")
    for n in d["sombra"]:
        s = slug(n)
        L.append(f"  --shadow-{s.removeprefix('sombra-')}: var({p}{s});")
    L.append(f"  --font-sans: var({p}fuente);")
    L.append("}")
    L.append("")
    L.append("/* Gradientes: Tailwind no tiene tema para ellos, así que cada uno es una utilidad bg-gradiente-* */")
    for n, t in d["gradiente"].items():
        if "css" in t:
            L.append(f"@utility bg-gradiente-{slug(n)} {{ background-image: var({p}gradiente-{slug(n)}); }}")
    L.append("")
    # En capa 'components' para que una utilidad de Tailwind pueda sobrescribirlos (el CSS sin capa le ganaría).
    L.append("/* Estilos de texto (equivalen 1:1 a los estilos de Figma) */")
    L.append("@layer components {")
    peso = {"Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700}
    for n, t in d["tipografia"]["estilos"].items():
        reglas = [f"font-family: var({p}fuente)", f"font-weight: {peso[t['peso']]}",
                  f"font-size: {t['tamano']}px", f"line-height: {t['interlineado_pct'] / 100:.2f}",
                  f"letter-spacing: {t['tracking_px']}px"]
        if t["caja"] == "UPPER":
            reglas.append("text-transform: uppercase")
        L.append(f"  .sgft-texto-{slug(n)} {{ {'; '.join(reglas)}; }}")
    L.append("}")
    return "\n".join(L) + "\n"


def cmd_css(args):
    css = generar_css()
    if "--salida" in args:
        ruta = Path(args[args.index("--salida") + 1])
        ruta.write_text(css, encoding="utf-8")
        print(f"CSS escrito en {ruta}")
    else:
        sys.stdout.write(css)
    return 0


def cmd_verificar(args):
    d = cargar()
    errores = []
    for grupo in ("color", "no_tokenizado"):
        for n, t in d[grupo].items():
            if not HEX.match(t.get("valor", "")):
                errores.append(f"{grupo}/{n}: valor '{t.get('valor')}' no es #RRGGBB")
    for n, t in d["color"].items():
        if not t.get("alcances"):
            errores.append(f"color/{n}: sin alcances")
        if "ALL_SCOPES" in t.get("alcances", []):
            errores.append(f"color/{n}: usa ALL_SCOPES")
        if not t.get("uso"):
            errores.append(f"color/{n}: sin descripción de uso")
    for n, t in d["tipografia"]["estilos"].items():
        if t["peso"] not in d["tipografia"]["pesos"]:
            errores.append(f"tipografía {n}: peso {t['peso']} no cargado")
    if "--css" in args:
        ruta = Path(args[args.index("--css") + 1])
        css = ruta.read_text(encoding="utf-8")
        p = d["$meta"]["prefijo_css"]
        for n, t in d["color"].items():
            m = re.search(rf"{re.escape(p)}color-{slug(n)}\s*:\s*([^;]+);", css)
            if not m:
                errores.append(f"CSS: falta {p}color-{slug(n)}")
            elif m.group(1).strip().upper() != valor_css(t).upper():
                errores.append(f"CSS: {p}color-{slug(n)} = {m.group(1).strip()} pero Figma dice {valor_css(t)}")
        for n, t in d["medida"].items():
            m = re.search(rf"{re.escape(p)}{slug(n)}\s*:\s*(\d+)px", css)
            if not m:
                errores.append(f"CSS: falta {p}{slug(n)}")
            elif int(m.group(1)) != t["valor"]:
                errores.append(f"CSS: {p}{slug(n)} = {m.group(1)}px pero Figma dice {t['valor']}px")
    if errores:
        print("✘ " + "\n✘ ".join(errores))
        return 1
    print(f"✔ tokens.json válido: {len(d['color'])} colores, {len(d['medida'])} medidas, "
          f"{len(d['tipografia']['estilos'])} estilos de texto, {len(d['sombra'])} sombras."
          + (" CSS sincronizado." if "--css" in args else ""))
    return 0


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, args = argv[0], argv[1:]
    funciones = {"contraste": cmd_contraste, "buscar": cmd_buscar, "css": cmd_css, "verificar": cmd_verificar}
    if cmd not in funciones:
        print(__doc__)
        return 1
    return funciones[cmd](args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
