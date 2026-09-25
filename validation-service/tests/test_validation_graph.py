import json
from decimal import Decimal

import httpx
import pytest

from app.graph.validation_graph import construir_grafo_de_validacion
from app.schemas import FacturaExtraida, Proveedor

TARIFA_IVA_VIGENTE = Decimal("15")
PROVEEDOR_DEL_CATALOGO = Proveedor(ruc="1790016919001", razon_social="CORPORACION FAVORITA C.A.")
FACTURA_VALIDA = {
    "ruc_proveedor": "1790016919001",
    "razon_social_proveedor": "CORP. FAVORITA",
    "numero_de_factura": "001-001-000000123",
    "fecha_de_emision": "2026-09-01",
    "lineas": [{"descripcion": "Arroz", "cantidad": "2", "precio_unitario": "50.00", "descuento": "0", "precio_total_sin_impuesto": "100.00"}],
    "subtotales_por_tarifa": {"15": "100.00"},
    "total_descuento": "0",
    "valor_iva": "15.00",
    "importe_total": "115.00",
}


def validar(factura: dict, proveedor_encontrado: Proveedor | None = PROVEEDOR_DEL_CATALOGO, codigo_de_respuesta: int = 200):
    solicitudes_enviadas = []

    def responder(solicitud: httpx.Request) -> httpx.Response:
        solicitudes_enviadas.append(solicitud)
        return httpx.Response(codigo_de_respuesta)

    transporte = httpx.MockTransport(responder)
    grafo = construir_grafo_de_validacion(
        lambda ruc, razon_social: proveedor_encontrado,
        httpx.Client(base_url="http://erp", transport=transporte),
        httpx.Client(base_url="http://excepciones", transport=transporte),
        TARIFA_IVA_VIGENTE,
    )
    estado_final = grafo.invoke({"factura": FacturaExtraida(**factura), "motivos_de_rechazo": []})
    return estado_final["motivos_de_rechazo"], solicitudes_enviadas


def test_factura_valida_se_envia_al_erp():
    motivos_de_rechazo, solicitudes_enviadas = validar(FACTURA_VALIDA)
    assert motivos_de_rechazo == []
    assert [str(solicitud.url) for solicitud in solicitudes_enviadas] == ["http://erp/facturas"]


def test_factura_con_errores_se_envia_a_excepciones_con_sus_motivos():
    factura = {**FACTURA_VALIDA, "ruc_proveedor": "1790016918001", "importe_total": "120.00"}
    motivos_de_rechazo, solicitudes_enviadas = validar(factura, Proveedor(ruc="1790016918001", razon_social="X"))
    cuerpo_enviado = json.loads(solicitudes_enviadas[0].content)
    assert motivos_de_rechazo == ["RUC del proveedor inválido", "Totales inconsistentes"]
    assert str(solicitudes_enviadas[0].url) == "http://excepciones/excepciones"
    assert cuerpo_enviado["motivos_de_rechazo"] == motivos_de_rechazo
    assert cuerpo_enviado["factura"]["ruc_proveedor"] == "1790016918001"


def test_proveedor_fuera_del_catalogo_se_envia_a_excepciones():
    motivos_de_rechazo, solicitudes_enviadas = validar(FACTURA_VALIDA, proveedor_encontrado=None)
    assert motivos_de_rechazo == ["El proveedor no está en el catálogo"]
    assert str(solicitudes_enviadas[0].url) == "http://excepciones/excepciones"


def test_ruc_que_no_coincide_con_el_proveedor_del_catalogo():
    proveedor_parecido = Proveedor(ruc="1760013210001", razon_social="CORPORACION FAVORITA C.A.")
    motivos_de_rechazo, _ = validar(FACTURA_VALIDA, proveedor_parecido)
    assert motivos_de_rechazo == ["El RUC 1790016919001 no coincide con el de CORPORACION FAVORITA C.A. (1760013210001)"]


def test_falla_del_servicio_destino_no_se_silencia():
    with pytest.raises(httpx.HTTPStatusError):
        validar(FACTURA_VALIDA, codigo_de_respuesta=500)
