import xmlrpc.client
import os
from dotenv import load_dotenv

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
    [[["supplier_rank", ">", 0]]],
    {"fields": ["id", "name", "vat"], "limit": 5}
)
print("Proveedores encontrados:", proveedores)

if not proveedores:
    raise Exception("No hay proveedores. Crea uno a mano en Odoo antes de seguir.")

proveedor_id = proveedores[0]["id"]

# --- 4. Prueba de escritura: crear una factura de proveedor por codigo ---
factura_id = models.execute_kw(
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

# --- 5. Confirmar leyendo de vuelta lo que se creo ---
factura = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    "account.move", "read",
    [[factura_id]],
    {"fields": ["name", "partner_id", "amount_total", "state"]}
)
print("Factura leida de vuelta:", factura)