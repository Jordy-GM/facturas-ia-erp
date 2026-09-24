"""
mcp_server.py

Servidor MCP (Model Context Protocol) que expone la lógica de
odoo_client.py como tools. Este es el puente entre erp-connector-service
y Odoo — pensado para que después extraction-service / validation-service
(o un agente LangGraph) lo consuman sin acoplarse al XML-RPC directamente.

Corre de forma aislada por ahora, sin depender de FastAPI ni de los
otros microservicios.
"""

from mcp.server.fastmcp import FastMCP

from app import odoo_client

mcp = FastMCP("erp-connector-service")

# Conexión única, reutilizada por todos los tools. Si falla al arrancar,
# preferimos que el servidor truene acá y no en cada llamada individual.
_conn = odoo_client.get_connection()


@mcp.tool()
def consultar_proveedor(ruc: str) -> dict:
    """
    Busca un proveedor en Odoo por su RUC.

    Args:
        ruc: RUC del proveedor, ya validado (módulo 11) por
            validation-service antes de llegar acá.

    Returns:
        {"encontrado": True, "partner_id": int} si existe,
        {"encontrado": False, "partner_id": None} si no.
    """
    partner_id = odoo_client.search_supplier(_conn, ruc)
    return {
        "encontrado": partner_id is not None,
        "partner_id": partner_id,
    }


@mcp.tool()
def crear_factura_proveedor(
    partner_id: int,
    invoice_date: str,
    document_number: str,
    lines: list,
    document_type_id: int = 1,
) -> dict:
    """
    Crea una factura de proveedor en Odoo en estado borrador.

    No la contabiliza — solo crea el registro. Contabilizar
    (action_post) queda como un paso/tool aparte una vez que
    este servidor esté validado de forma aislada.

    Args:
        partner_id: id del proveedor (res.partner), obtenido con
            consultar_proveedor.
        invoice_date: fecha en formato 'YYYY-MM-DD'.
        document_number: número de documento SRI, formato
            'establecimiento-puntoemision-secuencial'
            (ej: '001-001-000000123').
        lines: lista de dicts con al menos
            {'name': str, 'quantity': float, 'price_unit': float}.
        document_type_id: id de l10n_latam.document.type.
            Default 1 -> código '01' (Factura).

    Returns:
        {"invoice_id": int, "state": "draft", "name": str}
        o {"error": str} si Odoo rechaza la creación (ej: campos
        fiscales faltantes, proveedor inválido).
    """
    try:
        invoice_id = odoo_client.create_invoice(
            _conn,
            partner_id=partner_id,
            invoice_date=invoice_date,
            document_number=document_number,
            lines=lines,
            document_type_id=document_type_id,
        )
    except Exception as e:
        return {"error": str(e)}

    factura = odoo_client.read_invoice(_conn, invoice_id)
    return {
        "invoice_id": factura["id"],
        "state": factura["state"],
        "name": factura["name"],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")