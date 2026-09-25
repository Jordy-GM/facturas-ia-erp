import re
from typing import Callable

PATRON_RUC = re.compile(r"\d{13}")
CODIGO_ULTIMA_PROVINCIA = 24
CODIGO_ECUATORIANOS_EN_EL_EXTERIOR = 30
CODIGOS_DE_PROVINCIA = {f"{codigo:02d}" for codigo in [*range(1, CODIGO_ULTIMA_PROVINCIA + 1), CODIGO_ECUATORIANOS_EN_EL_EXTERIOR]}
LONGITUD_CODIGO_DE_PROVINCIA = 2
POSICION_TIPO_DE_CONTRIBUYENTE = 2
RESTA_A_PRODUCTOS_DE_DOS_DIGITOS = 9
COEFICIENTES_PERSONA_NATURAL = [2, 1, 2, 1, 2, 1, 2, 1, 2]
COEFICIENTES_SOCIEDAD_PUBLICA = [3, 2, 7, 6, 5, 4, 3, 2]
COEFICIENTES_SOCIEDAD_PRIVADA = [4, 3, 2, 7, 6, 5, 4, 3, 2]
MODULO_10 = 10
MODULO_11 = 11


def es_ruc_valido(ruc: str) -> bool:
    if not PATRON_RUC.fullmatch(ruc):
        return False
    if ruc[:LONGITUD_CODIGO_DE_PROVINCIA] not in CODIGOS_DE_PROVINCIA:
        return False
    match ruc[POSICION_TIPO_DE_CONTRIBUYENTE]:
        case "0" | "1" | "2" | "3" | "4" | "5":
            return tiene_digito_verificador_valido(ruc, COEFICIENTES_PERSONA_NATURAL, calcular_digito_modulo_10)
        case "6":
            return tiene_digito_verificador_valido(ruc, COEFICIENTES_SOCIEDAD_PUBLICA, calcular_digito_modulo_11)
        case "9":
            return tiene_digito_verificador_valido(ruc, COEFICIENTES_SOCIEDAD_PRIVADA, calcular_digito_modulo_11)
        case _:
            return False


def tiene_digito_verificador_valido(
    ruc: str, coeficientes: list[int], calcular_digito: Callable[[str, list[int]], int]
) -> bool:
    posicion_del_digito_verificador = len(coeficientes)
    establecimiento = ruc[posicion_del_digito_verificador + 1:]
    if int(establecimiento) == 0:
        return False
    return calcular_digito(ruc[:posicion_del_digito_verificador], coeficientes) == int(ruc[posicion_del_digito_verificador])


def calcular_digito_modulo_10(digitos: str, coeficientes: list[int]) -> int:
    productos = [int(digito) * coeficiente for digito, coeficiente in zip(digitos, coeficientes)]
    suma = sum(producto - RESTA_A_PRODUCTOS_DE_DOS_DIGITOS if producto >= MODULO_10 else producto for producto in productos)
    return (MODULO_10 - suma % MODULO_10) % MODULO_10


def calcular_digito_modulo_11(digitos: str, coeficientes: list[int]) -> int:
    residuo = sum(int(digito) * coeficiente for digito, coeficiente in zip(digitos, coeficientes)) % MODULO_11
    if residuo == 0:
        return 0
    return MODULO_11 - residuo
