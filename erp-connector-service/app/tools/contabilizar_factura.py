from typing import Annotated
from pydantic import Field

from app import odoo_client
from app.prompts import tool_descriptions as p

def register(mcp, _conn):
    # tool para contabilizar la factura, que es un paso aparte de la creación pasar la factura de borrador a estado posted
    @mcp.tool(name="contabilizar_factura", description=p.CONTABILIZAR_FACTURA_DESC)
    def contabilizar_factura(invoice_id: Annotated[int, Field(description=p.INVOICE_ID_PARAM)]) -> dict:
        """Ejecuta action_post sobre una factura en borrador y devuelve su estado."""
        try:
            factura = odoo_client.post_invoice(_conn, invoice_id)
        except Exception as e:
            return {"error": str(e)}

        return {
            "invoice_id": factura["id"],
            "state": factura["state"],
            "name": factura["name"],
        }