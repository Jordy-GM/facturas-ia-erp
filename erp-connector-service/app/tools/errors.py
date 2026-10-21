import logging

logger = logging.getLogger(__name__)

def error_response(e: Exception) -> dict: #Recibe la excepción capturada y devuelve un diccionario listo para enviar al agente.
    
    logger.exception("Fallo en tool mcp") #.exception(...) registra el mensaje con nivel ERROR y además incluye el traceback completo (el detalle de en qué línea falló y por qué)
    
    return {
        "ok": False, # el agente distingue éxito de error con un solo campo. True p False.
        "error_type": type(e).__name__, #Contiene el nombre de la clase de excepción.
        "detail": str(e), #el mensaje de la excepción, con el motivo concreto.
            }