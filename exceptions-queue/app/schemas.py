from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class OrigenEnum(str, Enum):
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    ERP_CONNECTOR = "erp-connector"


class EstadoEnum(str, Enum):
    PENDIENTE = "pendiente"
    RESUELTA = "resuelta"


class ExceptionCreate(BaseModel):
    origen: OrigenEnum = Field(
        ...,
        description="Servicio que reporta ('extraction', 'validation', 'erp-connector')",
    )
    tipo_error: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="String corto descriptivo del error (ej. ruc_invalido, odoo_post_failed)",
    )
    mensaje: str = Field(
        ...,
        min_length=1,
        description="Descripción legible del problema",
    )
    proveedor_ruc: Optional[str] = Field(
        default=None,
        max_length=20,
        description="RUC del proveedor (opcional)",
    )
    numero_documento: Optional[str] = Field(
        default=None,
        pattern=r"^\d{3}-\d{3}-\d{9}$",
        description="Número de documento SRI en formato 001-001-XXXXXXXXX (opcional)",
    )
    payload_original: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON libre con los datos de la factura tal como llegaron",
    )


class ExceptionResolveRequest(BaseModel):
    nota: Optional[str] = Field(
        default=None,
        description="Nota opcional sobre la resolución manual",
    )
    nota_resolucion: Optional[str] = Field(
        default=None,
        description="Alias de nota para mayor flexibilidad",
    )

    def get_nota(self) -> Optional[str]:
        if self.nota is not None:
            return self.nota
        return self.nota_resolucion


class ExceptionResponse(BaseModel):
    id: int
    origen: str
    tipo_error: str
    mensaje: str
    proveedor_ruc: Optional[str] = None
    numero_documento: Optional[str] = None
    payload_original: dict[str, Any] = Field(default_factory=dict)
    estado: str
    nota_resolucion: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
