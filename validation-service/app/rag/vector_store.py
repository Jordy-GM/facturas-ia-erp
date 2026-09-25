from typing import Callable

from sqlalchemy import Engine, text

from app.schemas import Proveedor

CONSULTA_PROVEEDORES_SIN_EMBEDDING = text("SELECT ruc, razon_social FROM proveedores WHERE embedding IS NULL")
ACTUALIZACION_DE_EMBEDDING = text("UPDATE proveedores SET embedding = CAST(:embedding AS vector) WHERE ruc = :ruc")
CONSULTA_PROVEEDOR_POR_RUC_O_SIMILITUD = text("""
    SELECT ruc, razon_social FROM proveedores
    WHERE ruc = :ruc OR embedding <=> CAST(:embedding AS vector) <= :distancia_maxima
    ORDER BY ruc = :ruc DESC, embedding <=> CAST(:embedding AS vector)
    LIMIT 1
""")


def indexar_proveedores_sin_embedding(motor: Engine, generar_embedding: Callable[[str], list[float]]) -> None:
    with motor.begin() as conexion:
        for proveedor in conexion.execute(CONSULTA_PROVEEDORES_SIN_EMBEDDING).all():
            conexion.execute(ACTUALIZACION_DE_EMBEDDING, {"embedding": str(generar_embedding(proveedor.razon_social)), "ruc": proveedor.ruc})


def buscar_proveedor_por_ruc_o_similitud(motor: Engine, ruc: str, embedding: list[float], distancia_maxima: float) -> Proveedor | None:
    with motor.connect() as conexion:
        proveedor_encontrado = conexion.execute(
            CONSULTA_PROVEEDOR_POR_RUC_O_SIMILITUD, {"ruc": ruc, "embedding": str(embedding), "distancia_maxima": distancia_maxima}
        ).first()
    if proveedor_encontrado is None:
        return None
    return Proveedor(ruc=proveedor_encontrado.ruc, razon_social=proveedor_encontrado.razon_social)
