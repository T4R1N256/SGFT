"""
Price of an order in integer cents (WBS 3.3.4). Owner: Jesús (rev. Tarín). Spanish names and keys by the approved
exception (DEC-01): the device sends the order with this same shape and static/pos/pricing.js has the mirror
calcularTotal(). Both must give the same result for every case of tests_fixtures/pricing_cases.json (parity test,
WBS 3.4.5); change all three in the same PR.

A line costs (precio_base_centavos + the ajuste_centavos of every "agregar" modifier) × cantidad. A "quitar"
modifier never changes the price; it only changes the inventory deduction (rule 2).
"""

MODIFIER_TYPES = ("agregar", "quitar")


def _entero(valor, campo, minimo):
    # bool is an int in Python; it is rejected so that True never counts as 1 (JS has no such case).
    if type(valor) is not int or valor < minimo:
        raise ValueError(f"{campo} debe ser un entero mayor o igual a {minimo}.")
    return valor


def calcular_total(pedido):
    """Total of pedido {"lineas": [...]} in cents. Raises ValueError if the order is malformed."""
    if not isinstance(pedido, dict) or not isinstance(pedido.get("lineas"), list):
        raise ValueError("El pedido debe traer una lista de líneas.")
    total = 0
    for linea in pedido["lineas"]:
        if not isinstance(linea, dict):
            raise ValueError("Cada línea debe ser un objeto.")
        base = _entero(linea.get("precio_base_centavos"), "precio_base_centavos", 0)
        cantidad = _entero(linea.get("cantidad"), "cantidad", 1)
        modificadores = linea.get("modificadores", [])
        if not isinstance(modificadores, list):
            raise ValueError("modificadores debe ser una lista.")
        extras = 0
        for modificador in modificadores:
            if not isinstance(modificador, dict) or modificador.get("tipo") not in MODIFIER_TYPES:
                raise ValueError('Cada modificador debe ser de tipo "agregar" o "quitar".')
            ajuste = _entero(modificador.get("ajuste_centavos", 0), "ajuste_centavos", 0)
            if modificador["tipo"] == "agregar":
                extras += ajuste
        total += (base + extras) * cantidad
    return total
