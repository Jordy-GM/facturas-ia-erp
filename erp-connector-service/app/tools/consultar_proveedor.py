from typing import Annotated
from pydantic import Field

from app import odoo_client
from app.prompts import tool_descriptions as p



def register(mcp, _conn):# Recibe mcp y conn por parámetro (en vez de importarlos de mcp_server.py) para evitar el import circular, y registra aquí la herramienta.
    @mcp.tool(name="consultar_proveedor", description=p.CONSULTAR_PROVEEDOR_DESC)
    def consultar_proveedor(ruc: Annotated[str, Field(description=p.RUC_PARAM)],) -> dict:
        """Busca res.partner por vat. Ver odoo_client.search_supplier."""
        try:
            partner_id = odoo_client.search_supplier(_conn, ruc)
            return {
                "encontrado": partner_id is not None,
                "partner_id": partner_id,
            }

        except Exception as e:
            return {"error": str(e)}
