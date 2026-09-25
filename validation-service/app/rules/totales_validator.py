from decimal import Decimal

from app.rules.iva_validator import son_montos_iguales
from app.schemas import LineaDeFactura


def son_totales_consistentes(
    lineas: list[LineaDeFactura],
    subtotales_por_tarifa: dict[Decimal, Decimal],
    total_descuento: Decimal,
    valor_iva: Decimal,
    importe_total: Decimal,
) -> bool:
    subtotal_sin_impuestos = sum(subtotales_por_tarifa.values())
    if not lineas:
        return False
    if not all(es_linea_consistente(linea) for linea in lineas):
        return False
    if not son_montos_iguales(sum(linea.descuento for linea in lineas), total_descuento):
        return False
    if not son_montos_iguales(sum(linea.precio_total_sin_impuesto for linea in lineas), subtotal_sin_impuestos):
        return False
    return son_montos_iguales(subtotal_sin_impuestos + valor_iva, importe_total)


def es_linea_consistente(linea: LineaDeFactura) -> bool:
    return son_montos_iguales(linea.cantidad * linea.precio_unitario - linea.descuento, linea.precio_total_sin_impuesto)
