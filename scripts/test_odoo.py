import xmlrpc.client
import os
from dotenv import load_dotenv
import random


load_dotenv()

##ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_URL = os.getenv("ODOO_URL_LOCAL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USERNAME = os.getenv("ODOO_USERNAME")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

# --- 1. Autenticacion ---
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})

if not uid:
    raise Exception("No se pudo autenticar. Revisa DB, usuario o password.")

print(f"Autenticado correctamente. uid = {uid}")

# --- 2. Conexion al endpoint de objetos ---
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

# --- 3. Prueba de lectura: buscar el proveedor que creaste a mano ---


proveedores = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    "res.partner", "search_read",
    [[["vat", "=", "58-0628465"]]],  # busca por RUC exacto
    {"fields": ["id", "name", "vat"]}
)
print("Proveedores encontrados:", proveedores)

if not proveedores:
    raise Exception("No hay proveedores. Crea uno a mano en Odoo antes de seguir.")

proveedor_id = proveedores[0]["id"]

# --- 4. Prueba de escritura: crear una factura de proveedor por codigo ---
"""factura_id = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    "account.move", "create",
    [{
        "move_type": "in_invoice",
        "partner_id": proveedor_id,
        "invoice_date": "2026-09-02",
        "ref": "TEST-SCRIPT-001",
        "invoice_line_ids": [
            (0, 0, {
                "name": "Servicio de prueba",
                "quantity": 1,
                "price_unit": 100.0,
            })
        ],
    }]
)
print(f"Factura creada con id: {factura_id}")
"""
numero_doc = f"001-001-{random.randint(100000, 999999)}"
factura_id = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    "account.move", "create",
    
    [{
        "move_type": "in_invoice",
        "partner_id": proveedor_id,
        "invoice_date": "2026-09-02",
        "ref": "TEST-SCRIPT-001",
        "l10n_latam_document_type_id": 1,  # "Invoice" / Factura, según lo que encontramos
        "l10n_latam_document_number": numero_doc,  # numero de ejemplo, formato SRI
        "invoice_line_ids": [
            (0, 0, {
                "name": "Servicio de prueba",
                "quantity": 1,
                "price_unit": 100.0,
            })
        ],
    }]
)


# --- 5. Confirmar leyendo de vuelta lo que se creo ---
factura = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    "account.move", "read",
    [[factura_id]],
    {"fields": ["name", "partner_id", "amount_total", "state"]}
)
print("Factura leida de vuelta:", factura)


"""
# Ver todos los tipos de documento disponibles
tipos_doc = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    "l10n_latam.document.type", "search_read",
    [[]],  # sin filtro, trae todos
    {"fields": ["id", "name", "code", "country_id"], "limit": 50}
)
for t in tipos_doc:
    print(t)
    
"""

#---6. contabilizar la factura (pasar de Borrador a Publicado)}
models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    "account.move", "action_post",
    [[factura_id]]      )

# --- 7. Releer la factura para ver que cambio de estado ---
factura = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    "account.move", "read",
    [[factura_id]],
    {"fields": ["name", "partner_id", "amount_total", "state"]}
)
print("Factura después de action_post:", factura)