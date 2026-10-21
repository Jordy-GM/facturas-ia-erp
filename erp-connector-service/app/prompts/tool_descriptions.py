"""
Textos que lee el LLM para decidir cuándo y cómo usar cada tool.
Si cambia el comportamiento de una tool en mcp_server.py, actualizá
también su descripción acá.
"""

CONSULTAR_PROVEEDOR_DESC = """
Busca un proveedor en Odoo por su RUC.
Devuelve {"encontrado": bool, "partner_id": int | null}.
Usala SIEMPRE antes de crear una factura: el partner_id que devuelve
es el que necesita crear_factura_proveedor.
Si encontrado es false, NO crees la factura; derivala a la cola de excepciones.
"""

CREAR_FACTURA_DESC = """
Crea una factura de proveedor en Odoo en estado BORRADOR. No la contabiliza.
Usala solo si la factura ya pasó la validación (RUC, IVA, totales) y
tenés el partner_id obtenido con consultar_proveedor.
Devuelve {"invoice_id", "state", "name"}, o {"error": str} si Odoo la
rechaza (por ejemplo, campos fiscales faltantes). Si hay error, no
reintentes a ciegas: derivá la factura a la cola de excepciones.
"""

CONTABILIZAR_FACTURA_DESC = """
    "Contabiliza (publica) una factura de proveedor que está en borrador. "
    "Devuelve el estado final leído de Odoo: si state es 'posted', quedó contabilizada. "
    "Si Odoo la rechaza (por ejemplo, falta cuenta contable o datos fiscales), "
    "devuelve el detalle del error y la factura queda en borrador."
"""


# Descripciones de parámetros
RUC_PARAM = "RUC del proveedor, ya validado con módulo 11."
PARTNER_ID_PARAM = "ID del proveedor en Odoo (res.partner), obtenido con consultar_proveedor."
INVOICE_DATE_PARAM = "Fecha de la factura en formato YYYY-MM-DD."
DOC_NUMBER_PARAM = "Número SRI con formato 001-001-000000123."
LINES_PARAM = "Líneas de la factura: lista de dicts con name (str), quantity (float) y price_unit (float)."
DOC_TYPE_PARAM = "ID del tipo de documento l10n_latam. Por defecto 1 (código 01, Factura)."
INVOICE_ID_PARAM = "ID de la factura (account.move) devuelto por crear_factura_proveedor."