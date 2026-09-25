from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

LONGITUD_MAXIMA_DE_TEXTO_SRI = 300


class LineaDeFactura(BaseModel):
    descripcion: str = Field(max_length=LONGITUD_MAXIMA_DE_TEXTO_SRI)
    cantidad: Decimal
    precio_unitario: Decimal
    descuento: Decimal = Decimal("0")
    precio_total_sin_impuesto: Decimal


class FacturaExtraida(BaseModel):
    ruc_proveedor: str
    razon_social_proveedor: str = Field(max_length=LONGITUD_MAXIMA_DE_TEXTO_SRI)
    numero_de_factura: str
    fecha_de_emision: date
    lineas: list[LineaDeFactura]
    subtotales_por_tarifa: dict[Decimal, Decimal]
    total_descuento: Decimal = Decimal("0")
    valor_iva: Decimal
    importe_total: Decimal


class Proveedor(BaseModel):
    ruc: str
    razon_social: str


class ResultadoDeValidacion(BaseModel):
    es_valida: bool
    motivos_de_rechazo: list[str]
