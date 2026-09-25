from datetime import datetime, timezone
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExceptionRecord(Base):
    __tablename__ = "exceptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    origen = Column(String(50), nullable=False, index=True)
    tipo_error = Column(String(100), nullable=False, index=True)
    mensaje = Column(Text, nullable=False)
    proveedor_ruc = Column(String(20), nullable=True, index=True)
    numero_documento = Column(String(50), nullable=True, index=True)
    payload_original = Column(JSON, nullable=False, default=dict)
    estado = Column(String(20), nullable=False, default="pendiente", index=True)
    nota_resolucion = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)
