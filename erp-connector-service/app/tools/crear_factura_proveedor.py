from typing import Annotated
from pydantic import Field

from app import odoo_client
from app.prompts import tool_descriptions as p
from app.tools.errors import error_response
from pydantic import BaseModel, Field

class LineaFactura(BaseModel):
    name: str
    quantity: float = 1
    price_unit: float
    account_id: int | None = None

def register(mcp, _conn):
    
    @mcp.tool(name="crear_factura_proveedor", description=p.CREAR_FACTURA_DESC)
    def crear_factura_proveedor(
        #Aquí se especifican los datos que necesita para crear la factura.
        partner_id: Annotated[int, Field(description=p.PARTNER_ID_PARAM)], #Identificador del proveedor en Odoo.
        invoice_date: Annotated[str, Field(description=p.INVOICE_DATE_PARAM)], #Fecha de la factura, representada como texto.
        document_number: Annotated[str, Field(description=p.DOC_NUMBER_PARAM)], #Número del documento del proveedor.
        lines: Annotated[list[LineaFactura], Field(description=p.LINES_PARAM)], #Lista de líneas de la factura, cada línea es un diccionario con detalles como producto, cantidad, precio, etc.
        document_type_id: Annotated[int, Field(description=p.DOC_TYPE_PARAM)] = 1, #Identificador del tipo de documento en Odoo, con un valor predeterminado de 1.
    ) -> dict:
        """Crea account.move in_invoice en draft. Contabilizar queda como tool aparte."""
        try:
            # Aquí se llama a la función create_invoice del módulo odoo_client para crear la factura en Odoo.
            invoice_id = odoo_client.create_invoice( 
                _conn, # Conexión a Odoo
                partner_id=partner_id, #El id del proveedor.
                invoice_date=invoice_date, #La fecha de la factura.
                document_number=document_number, #El número del documento del proveedor.
                #lines=lines, Las líneas de la factura, que contienen detalles como producto, cantidad, precio, etc.
                lines=[line.model_dump(exclude_none=True) for line in lines], #convierte cada línea de la factura de nuevo en un diccionario, excluyendo los valores None.
                document_type_id=document_type_id, #El id del tipo de documento en Odoo, con un valor predeterminado de 1.
            )
            
            factura = odoo_client.read_invoice(_conn, invoice_id) #Lee la factura recién creada en Odoo para obtener sus detalles.
            return {
                "ok": True,
                "invoice_id": factura["id"],
                "state": factura["state"],
                "name": factura["name"],
            }
            
        except Exception as e:
            return error_response(e)
