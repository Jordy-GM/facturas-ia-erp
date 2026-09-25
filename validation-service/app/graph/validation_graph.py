import operator
from decimal import Decimal
from typing import Annotated, Callable, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph

from app.rules.iva_validator import es_iva_valido
from app.rules.ruc_validator import es_ruc_valido
from app.rules.totales_validator import son_totales_consistentes
from app.schemas import FacturaExtraida, Proveedor

RUTA_DE_FACTURAS_EN_ERP = "/facturas"
RUTA_DE_EXCEPCIONES = "/excepciones"


class EstadoDeValidacion(TypedDict):
    factura: FacturaExtraida
    motivos_de_rechazo: Annotated[list[str], operator.add]


def construir_grafo_de_validacion(
    buscar_proveedor: Callable[[str, str], Proveedor | None],
    cliente_erp: httpx.Client,
    cliente_de_excepciones: httpx.Client,
    tarifa_iva_vigente: Decimal,
):
    def validar_reglas_sri(estado: EstadoDeValidacion) -> dict:
        factura = estado["factura"]
        cumplimiento_por_motivo = {
            "RUC del proveedor inválido": es_ruc_valido(factura.ruc_proveedor),
            "IVA inconsistente o con tarifa no vigente": es_iva_valido(factura.subtotales_por_tarifa, factura.valor_iva, tarifa_iva_vigente),
            "Totales inconsistentes": son_totales_consistentes(
                factura.lineas, factura.subtotales_por_tarifa, factura.total_descuento, factura.valor_iva, factura.importe_total
            ),
        }
        return {"motivos_de_rechazo": [motivo for motivo, cumple in cumplimiento_por_motivo.items() if not cumple]}

    def identificar_proveedor(estado: EstadoDeValidacion) -> dict:
        factura = estado["factura"]
        proveedor = buscar_proveedor(factura.ruc_proveedor, factura.razon_social_proveedor)
        if proveedor is None:
            return {"motivos_de_rechazo": ["El proveedor no está en el catálogo"]}
        if proveedor.ruc != factura.ruc_proveedor:
            return {"motivos_de_rechazo": [f"El RUC {factura.ruc_proveedor} no coincide con el de {proveedor.razon_social} ({proveedor.ruc})"]}
        return {"motivos_de_rechazo": []}

    def enviar_al_erp(estado: EstadoDeValidacion) -> None:
        cliente_erp.post(RUTA_DE_FACTURAS_EN_ERP, json=estado["factura"].model_dump(mode="json")).raise_for_status()

    def enviar_a_excepciones(estado: EstadoDeValidacion) -> None:
        excepcion = {"factura": estado["factura"].model_dump(mode="json"), "motivos_de_rechazo": estado["motivos_de_rechazo"]}
        cliente_de_excepciones.post(RUTA_DE_EXCEPCIONES, json=excepcion).raise_for_status()

    def elegir_destino(estado: EstadoDeValidacion) -> str:
        if estado["motivos_de_rechazo"]:
            return "enviar_a_excepciones"
        return "enviar_al_erp"

    grafo = StateGraph(EstadoDeValidacion)
    grafo.add_node("validar_reglas_sri", validar_reglas_sri)
    grafo.add_node("identificar_proveedor", identificar_proveedor)
    grafo.add_node("enviar_al_erp", enviar_al_erp)
    grafo.add_node("enviar_a_excepciones", enviar_a_excepciones)
    grafo.add_edge(START, "validar_reglas_sri")
    grafo.add_edge("validar_reglas_sri", "identificar_proveedor")
    grafo.add_conditional_edges("identificar_proveedor", elegir_destino, ["enviar_al_erp", "enviar_a_excepciones"])
    grafo.add_edge("enviar_al_erp", END)
    grafo.add_edge("enviar_a_excepciones", END)
    return grafo.compile()
