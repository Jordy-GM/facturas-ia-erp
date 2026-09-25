from typing import Callable

from sqlalchemy import Engine

from app.rag.vector_store import buscar_proveedor_por_ruc_o_similitud
from app.schemas import Proveedor

DISTANCIA_COSENO_MAXIMA = 0.4


def crear_buscador_de_proveedores(motor: Engine, generar_embedding: Callable[[str], list[float]]) -> Callable[[str, str], Proveedor | None]:
    return lambda ruc, razon_social: buscar_proveedor_por_ruc_o_similitud(motor, ruc, generar_embedding(razon_social), DISTANCIA_COSENO_MAXIMA)
