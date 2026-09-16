"""
odoo_client.py

Cliente XML-RPC para Odoo 16 Community. Encapsula las operaciones
de autenticación, búsqueda de proveedores y gestión de facturas
de proveedor (account.move, tipo in_invoice).

Este módulo es la capa que después el servidor MCP va a envolver
como tools (search_supplier, create_invoice, post_invoice, etc).
"""

import os
import xmlrpc.client
from typing import Optional


# ---------------------------------------------------------------------
# Conexión / autenticación
# ---------------------------------------------------------------------

class OdooConnection:
    """
    Agrupa la conexión autenticada a Odoo (uid + proxy de models)
    para no tener que repetir db/uid/password en cada función.
    """

    def __init__(self):
        self.url = os.getenv("ODOO_URL")
        self.db = os.getenv("ODOO_DB")
        self.username = os.getenv("ODOO_USERNAME")
        self.password = os.getenv("ODOO_PASSWORD")

        if not all([self.url, self.db, self.username, self.password]):
            raise ValueError(
                "Faltan variables de entorno de Odoo "
                "(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)"
            )

        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = common.authenticate(self.db, self.username, self.password, {})

        if not self.uid:
            raise ConnectionError("Autenticación con Odoo falló (uid no obtenido)")

        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def execute_kw(self, model: str, method: str, args: list, kwargs: dict = None):
        """Wrapper corto para no repetir db/uid/password en cada llamada."""
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, method, args, kwargs or {}
        )


def get_connection() -> OdooConnection:
    """Punto de entrada único para obtener una conexión autenticada."""
    return OdooConnection()


# ---------------------------------------------------------------------
# Proveedores
# ---------------------------------------------------------------------

def search_supplier(conn: OdooConnection, ruc: str) -> Optional[int]:
    """
    Busca un proveedor (res.partner) por su VAT/RUC.
    Devuelve el partner_id, o None si no existe.

    Nota: en Odoo el campo estándar es 'vat', no 'ruc'. Se filtra
    exacto porque el RUC ya viene validado (modulo 11) desde
    validation-service antes de llegar acá.
    """
    partner_ids = conn.execute_kw(
        "res.partner", "search",
        [[["vat", "=", ruc]]]
    )
    return partner_ids[0] if partner_ids else None


# ---------------------------------------------------------------------
# Facturas de proveedor (account.move, in_invoice)
# ---------------------------------------------------------------------

def create_invoice(
    conn: OdooConnection,
    partner_id: int,
    invoice_date: str,
    document_number: str,
    lines: list,
    document_type_id: int = 1,
) -> int:
    """
    Crea una factura de proveedor en estado borrador.

    Args:
        partner_id: id del proveedor (res.partner), ya resuelto
            con search_supplier.
        invoice_date: fecha en formato 'YYYY-MM-DD'.
        document_number: número de documento SRI, formato
            'establecimiento-puntoemision-secuencial'
            (ej: '001-001-000000123'). Obligatorio por l10n_ec
            antes de poder contabilizar.
        lines: lista de dicts, cada uno con al menos
            {'name': str, 'quantity': float, 'price_unit': float}.
            Se pueden agregar 'account_id' si no querés depender
            de la cuenta por defecto del producto/proveedor.
        document_type_id: id de l10n_latam.document.type.
            Default 1 -> código '01' (Factura).

    Returns:
        El id de la factura creada (account.move, en estado draft).
    """
    invoice_lines = [
        (0, 0, {
            "name": line["name"],
            "quantity": line["quantity"],
            "price_unit": line["price_unit"],
        })
        for line in lines
    ]

    invoice_id = conn.execute_kw(
        "account.move", "create",
        [{
            "move_type": "in_invoice",
            "partner_id": partner_id,
            "invoice_date": invoice_date,
            "l10n_latam_document_type_id": document_type_id,
            "l10n_latam_document_number": document_number,
            "invoice_line_ids": invoice_lines,
        }]
    )
    return invoice_id


def read_invoice(conn: OdooConnection, invoice_id: int) -> dict:
    """Lee una factura y devuelve los campos relevantes para validación/logs."""
    result = conn.execute_kw(
        "account.move", "read",
        [[invoice_id]],
        {"fields": ["id", "name", "state", "amount_total", "partner_id"]}
    )
    return result[0] if result else {}


def post_invoice(conn: OdooConnection, invoice_id: int) -> dict:
    """
    Contabiliza (action_post) una factura en borrador.

    action_post no devuelve un valor útil, así que después de
    llamarlo se vuelve a leer la factura para confirmar el
    cambio de estado draft -> posted y obtener el folio asignado.

    Lanza RuntimeError con el mensaje original de Odoo si la
    contabilización falla (ej: falta cuenta contable, documento
    fiscal incompleto, etc). El manejo de qué hacer con esa falla
    (mandar a exceptions-queue) queda para la capa de servicio,
    no para este cliente.
    """
    try:
        conn.execute_kw(
            "account.move", "action_post",
            [[invoice_id]]
        )
    except xmlrpc.client.Fault as e:
        raise RuntimeError(f"No se pudo contabilizar factura {invoice_id}: {e.faultString}") from e

    return read_invoice(conn, invoice_id)