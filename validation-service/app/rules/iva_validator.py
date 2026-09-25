from decimal import ROUND_HALF_UP, Decimal

TARIFA_IVA_CERO = Decimal("0")
TOLERANCIA_DE_REDONDEO = Decimal("0.01")
CENTAVOS = Decimal("0.01")
CIEN = Decimal("100")


def es_iva_valido(subtotales_por_tarifa: dict[Decimal, Decimal], valor_iva: Decimal, tarifa_iva_vigente: Decimal) -> bool:
    if not subtotales_por_tarifa.keys() <= {TARIFA_IVA_CERO, tarifa_iva_vigente}:
        return False
    iva_esperado = sum(calcular_iva(subtotal, tarifa) for tarifa, subtotal in subtotales_por_tarifa.items())
    return son_montos_iguales(iva_esperado, valor_iva)


def calcular_iva(subtotal: Decimal, tarifa: Decimal) -> Decimal:
    return (subtotal * tarifa / CIEN).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def son_montos_iguales(monto_calculado: Decimal, monto_declarado: Decimal) -> bool:
    return abs(monto_calculado - monto_declarado) <= TOLERANCIA_DE_REDONDEO
