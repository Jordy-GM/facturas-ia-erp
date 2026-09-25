from decimal import Decimal

import pytest

from app.rules.iva_validator import es_iva_valido
from app.rules.ruc_validator import es_ruc_valido
from app.rules.totales_validator import son_totales_consistentes
from app.schemas import LineaDeFactura

RUC_PERSONA_NATURAL = "1710034065001"
RUC_SOCIEDAD_PUBLICA = "1760013210001"
RUC_SOCIEDAD_PRIVADA = "1790016919001"
TARIFA_IVA_VIGENTE = Decimal("15")


def crear_linea(cantidad: str, precio_unitario: str, descuento: str, precio_total_sin_impuesto: str) -> LineaDeFactura:
    return LineaDeFactura(
        descripcion="Producto", cantidad=cantidad, precio_unitario=precio_unitario, descuento=descuento, precio_total_sin_impuesto=precio_total_sin_impuesto
    )


@pytest.mark.parametrize("ruc", [RUC_PERSONA_NATURAL, RUC_SOCIEDAD_PUBLICA, RUC_SOCIEDAD_PRIVADA])
def test_ruc_valido_por_tipo_de_contribuyente(ruc):
    assert es_ruc_valido(ruc)


@pytest.mark.parametrize("ruc", [
    "1710034064001",
    "1760013220001",
    "1790016918001",
    "171003406500",
    "17100340650011",
    "17100340650A1",
    " 1710034065001",
    "",
    "2510034065001",
    "0010034065001",
    "1770016919001",
    "1780016919001",
    "1710034065000",
    "1760013210000",
    "1790016919000",
])
def test_ruc_invalido(ruc):
    assert not es_ruc_valido(ruc)


def test_ruc_con_tipo_incorrecto_lanza_error():
    with pytest.raises(TypeError):
        es_ruc_valido(1790016919001)


def test_iva_valido_con_tarifas_0_y_15():
    assert es_iva_valido({Decimal("0"): Decimal("10.00"), Decimal("15"): Decimal("100.00")}, Decimal("15.00"), TARIFA_IVA_VIGENTE)


def test_iva_tolera_un_centavo_de_redondeo():
    assert es_iva_valido({Decimal("15"): Decimal("10.33")}, Decimal("1.56"), TARIFA_IVA_VIGENTE)


def test_iva_con_valor_incorrecto():
    assert not es_iva_valido({Decimal("15"): Decimal("100.00")}, Decimal("12.00"), TARIFA_IVA_VIGENTE)


@pytest.mark.parametrize("tarifa", [Decimal("5"), Decimal("8"), Decimal("12")])
def test_iva_con_tarifa_no_vigente(tarifa):
    assert not es_iva_valido({tarifa: Decimal("100.00")}, tarifa, TARIFA_IVA_VIGENTE)


def test_iva_con_montos_en_float_lanza_error():
    with pytest.raises(TypeError):
        es_iva_valido({Decimal("15"): 100.0}, Decimal("15.00"), TARIFA_IVA_VIGENTE)


def test_totales_consistentes_con_descuento():
    lineas = [crear_linea("2", "30.00", "0.00", "60.00"), crear_linea("1", "50.00", "10.00", "40.00"), crear_linea("1", "10.00", "0.00", "10.00")]
    assert son_totales_consistentes(
        lineas, {Decimal("15"): Decimal("100.00"), Decimal("0"): Decimal("10.00")}, Decimal("10.00"), Decimal("15.00"), Decimal("125.00")
    )


def test_totales_con_linea_mal_calculada():
    lineas = [crear_linea("2", "30.00", "0.00", "50.00")]
    assert not son_totales_consistentes(lineas, {Decimal("15"): Decimal("50.00")}, Decimal("0.00"), Decimal("7.50"), Decimal("57.50"))


def test_totales_con_descuento_total_incorrecto():
    lineas = [crear_linea("1", "50.00", "10.00", "40.00")]
    assert not son_totales_consistentes(lineas, {Decimal("15"): Decimal("40.00")}, Decimal("0.00"), Decimal("6.00"), Decimal("46.00"))


def test_totales_con_lineas_que_no_suman_el_subtotal():
    lineas = [crear_linea("1", "60.00", "0.00", "60.00"), crear_linea("1", "30.00", "0.00", "30.00")]
    assert not son_totales_consistentes(lineas, {Decimal("15"): Decimal("100.00")}, Decimal("0.00"), Decimal("15.00"), Decimal("115.00"))


def test_totales_con_importe_total_incorrecto():
    lineas = [crear_linea("1", "100.00", "0.00", "100.00")]
    assert not son_totales_consistentes(lineas, {Decimal("15"): Decimal("100.00")}, Decimal("0.00"), Decimal("15.00"), Decimal("120.00"))


def test_totales_sin_lineas():
    assert not son_totales_consistentes([], {}, Decimal("0"), Decimal("0"), Decimal("0"))
