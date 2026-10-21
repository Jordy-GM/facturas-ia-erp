from typing import Annotated
from pydantic import Field

from app import odoo_client
from app.prompts import tool_descriptions as p

def register(mcp, _conn):
    
    @mcp.tool(name="crear_factura_proveedor", description=p.CREAR_FACTURA_DESC)
    def crear_factura_proveedor(
        partner_id: Annotated[int, Field(description=p.PARTNER_ID_PARAM)],
        invoice_date: Annotated[str, Field(description=p.INVOICE_DATE_PARAM)],
        document_number: Annotated[str, Field(description=p.DOC_NUMBER_PARAM)],
        lines: Annotated[list, Field(description=p.LINES_PARAM)],
        document_type_id: Annotated[int, Field(description=p.DOC_TYPE_PARAM)] = 1,
    ) -> dict:
        """Crea account.move in_invoice en draft. Contabilizar queda como tool aparte."""
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