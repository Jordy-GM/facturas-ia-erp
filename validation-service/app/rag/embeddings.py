from typing import Callable

from sentence_transformers import SentenceTransformer


def crear_generador_de_embeddings(nombre_del_modelo: str) -> Callable[[str], list[float]]:
    modelo = SentenceTransformer(nombre_del_modelo)
    return lambda texto: modelo.encode(texto, normalize_embeddings=True).tolist()
