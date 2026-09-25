from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import Body, Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models import ExceptionRecord
from app.schemas import (
    EstadoEnum,
    ExceptionCreate,
    ExceptionResolveRequest,
    ExceptionResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa las tablas si no existen (en desarrollo o arranque de contenedor)
    try:
        init_db()
    except Exception as e:
        # En caso de que la BD aún esté arrancando o sea manejada externamente
        print(f"[exceptions-queue] Warning al inicializar DB: {e}")
    yield


app = FastAPI(
    title="exceptions-queue",
    description="Servicio de cola de facturas con excepciones para revisión manual",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Salud"])
def health_check():
    """Verifica que el servicio esté operativo."""
    return {"status": "ok", "service": "exceptions-queue"}


@app.post(
    "/exceptions",
    response_model=ExceptionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Excepciones"],
)
def create_exception(
    payload: ExceptionCreate,
    db: Session = Depends(get_db),
):
    """
    Registra una nueva excepción de factura reportada por cualquiera de los servicios
    (extraction, validation, erp-connector). Estado inicial: pendiente.
    """
    record = ExceptionRecord(
        origen=payload.origen.value if hasattr(payload.origen, "value") else str(payload.origen),
        tipo_error=payload.tipo_error,
        mensaje=payload.mensaje,
        proveedor_ruc=payload.proveedor_ruc,
        numero_documento=payload.numero_documento,
        payload_original=payload.payload_original,
        estado=EstadoEnum.PENDIENTE.value,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get(
    "/exceptions",
    response_model=list[ExceptionResponse],
    tags=["Excepciones"],
)
def list_exceptions(
    estado: Optional[str] = Query(
        default=None,
        description="Filtro opcional por estado (ej. pendiente, resuelta)",
    ),
    origen: Optional[str] = Query(
        default=None,
        description="Filtro opcional por servicio origen (ej. extraction, validation, erp-connector)",
    ),
    db: Session = Depends(get_db),
):
    """
    Lista las excepciones registradas, permitiendo filtros opcionales por estado y origen.
    """
    query = db.query(ExceptionRecord)

    if estado:
        query = query.filter(ExceptionRecord.estado == estado)
    if origen:
        query = query.filter(ExceptionRecord.origen == origen)

    return query.order_by(ExceptionRecord.created_at.desc()).all()


@app.get(
    "/exceptions/{id}",
    response_model=ExceptionResponse,
    tags=["Excepciones"],
)
def get_exception(
    id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene el detalle completo de una excepción específica por su ID.
    """
    record = db.query(ExceptionRecord).filter(ExceptionRecord.id == id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Excepción con ID {id} no encontrada",
        )
    return record


@app.patch(
    "/exceptions/{id}/resolver",
    response_model=ExceptionResponse,
    tags=["Excepciones"],
)
def resolve_exception(
    id: int,
    body: Optional[ExceptionResolveRequest] = Body(default=None),
    db: Session = Depends(get_db),
):
    """
    Marca una excepción como resuelta y guarda una nota opcional de resolución.
    No permite resolver una excepción que ya se encuentre resuelta.
    """
    record = db.query(ExceptionRecord).filter(ExceptionRecord.id == id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Excepción con ID {id} no encontrada",
        )

    if record.estado == EstadoEnum.RESUELTA.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La excepción ya fue resuelta",
        )

    record.estado = EstadoEnum.RESUELTA.value
    if body:
        record.nota_resolucion = body.get_nota()
    record.resolved_at = datetime.now(timezone.utc)
    record.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(record)
    return record
