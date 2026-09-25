from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from sqlalchemy import create_engine

from app.config import settings
from app.graph.validation_graph import construir_grafo_de_validacion
from app.rag.embeddings import crear_generador_de_embeddings
from app.rag.retriever import crear_buscador_de_proveedores
from app.rag.vector_store import indexar_proveedores_sin_embedding
from app.rules.iva_validator import CIEN
from app.schemas import FacturaExtraida, ResultadoDeValidacion


@asynccontextmanager
async def iniciar_servicio(app: FastAPI):
    motor = create_engine(settings.database_url)
    generar_embedding = crear_generador_de_embeddings(settings.embedding_model)
    indexar_proveedores_sin_embedding(motor, generar_embedding)
    with (
        httpx.Client(base_url=settings.erp_connector_service_url) as cliente_erp,
        httpx.Client(base_url=settings.exceptions_queue_url) as cliente_de_excepciones,
    ):
        app.state.grafo_de_validacion = construir_grafo_de_validacion(
            crear_buscador_de_proveedores(motor, generar_embedding), cliente_erp, cliente_de_excepciones, settings.iva_rate * CIEN
        )
        yield
    motor.dispose()


app = FastAPI(title="validation-service", lifespan=iniciar_servicio)


@app.post("/validar", response_model=ResultadoDeValidacion)
def validar_factura(factura: FacturaExtraida, request: Request) -> ResultadoDeValidacion:
    estado_final = request.app.state.grafo_de_validacion.invoke({"factura": factura, "motivos_de_rechazo": []})
    return ResultadoDeValidacion(es_valida=not estado_final["motivos_de_rechazo"], motivos_de_rechazo=estado_final["motivos_de_rechazo"])
