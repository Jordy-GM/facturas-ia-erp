"""
mcp_server.py

Servidor MCP (Model Context Protocol) que expone la lógica de
odoo_client.py como tools. Este es el puente entre erp-connector-service
y Odoo — pensado para que después extraction-service / validation-service
(o un agente LangGraph) lo consuman sin acoplarse al XML-RPC directamente.

Corre de forma aislada por ahora, sin depender de FastAPI ni de los
otros microservicios.
"""
from typing import Annotated
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from app import odoo_client
from app.prompts import tool_descriptions as p

from app.tools import consultar_proveedor, crear_factura_proveedor, contabilizar_factura
mcp = FastMCP("erp-connector-service")

# Conexión única, reutilizada por todos los tools. Si falla al arrancar,
# preferimos que el servidor truene acá y no en cada llamada individual.
_conn = odoo_client.get_connection()

crear_factura_proveedor.register(mcp, _conn)
consultar_proveedor.register(mcp, _conn)
contabilizar_factura.register(mcp, _conn)









if __name__ == "__main__":
    mcp.run(transport="stdio")