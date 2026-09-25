from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Verifica que el endpoint de salud responda con 200 y status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "exceptions-queue"


def test_create_exception_valid(client: TestClient):
    """Verifica creación de excepción con payload completo y válido."""
    payload = {
        "origen": "validation",
        "tipo_error": "ruc_invalido",
        "mensaje": "El RUC 1790011223001 falló la validación de módulo 11 del SRI",
        "proveedor_ruc": "1790011223001",
        "numero_documento": "001-001-000012345",
        "payload_original": {
            "ruc": "1790011223001",
            "razon_social": "EMPRESA PRUEBA S.A.",
            "total": 125.50,
        },
    }

    response = client.post("/exceptions", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["estado"] == "pendiente"
    assert data["created_at"] is not None
    assert data["origen"] == "validation"
    assert data["tipo_error"] == "ruc_invalido"
    assert (
        data["mensaje"]
        == "El RUC 1790011223001 falló la validación de módulo 11 del SRI"
    )
    assert data["proveedor_ruc"] == "1790011223001"
    assert data["numero_documento"] == "001-001-000012345"
    assert data["payload_original"]["total"] == 125.50
    assert data["nota_resolucion"] is None
    assert data["resolved_at"] is None


def test_create_exception_optional_fields(client: TestClient):
    """Verifica creación con campos opcionales omitidos."""
    payload = {
        "origen": "extraction",
        "tipo_error": "datos_ilegibles",
        "mensaje": "No se pudo extraer el total de la imagen",
    }

    response = client.post("/exceptions", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["estado"] == "pendiente"
    assert data["proveedor_ruc"] is None
    assert data["numero_documento"] is None
    assert data["payload_original"] == {}


def test_create_exception_invalid_origen(client: TestClient):
    """Verifica que un origen no permitido retorne 422 con detalle."""
    payload = {
        "origen": "servicio_desconocido",
        "tipo_error": "error_generico",
        "mensaje": "Mensaje de prueba",
    }

    response = client.post("/exceptions", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_exception_invalid_document_number_format(client: TestClient):
    """Verifica que un número de documento con formato incorrecto retorne 422."""
    payload = {
        "origen": "erp-connector",
        "tipo_error": "odoo_post_failed",
        "mensaje": "Fallo al enviar a Odoo",
        "numero_documento": "123-456",  # formato inválido (debe ser 001-001-XXXXXXXXX)
    }

    response = client.post("/exceptions", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_exception_missing_required_fields(client: TestClient):
    """Verifica que campos requeridos faltantes retornen 422."""
    response = client.post("/exceptions", json={})
    assert response.status_code == 422


def test_get_exception_by_id(client: TestClient):
    """Verifica la obtención de una excepción por su ID."""
    created = client.post(
        "/exceptions",
        json={
            "origen": "extraction",
            "tipo_error": "ocr_failed",
            "mensaje": "Fallo OCR",
        },
    ).json()

    exc_id = created["id"]
    response = client.get(f"/exceptions/{exc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == exc_id
    assert data["tipo_error"] == "ocr_failed"


def test_get_exception_not_found(client: TestClient):
    """Verifica que buscar una excepción inexistente retorne 404."""
    response = client.get("/exceptions/99999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_list_exceptions_and_filters(client: TestClient):
    """Verifica el listado de excepciones y filtrado por estado y origen."""
    # Crear 3 excepciones con distintas combinaciones
    client.post(
        "/exceptions",
        json={
            "origen": "extraction",
            "tipo_error": "ocr_error",
            "mensaje": "Error en OCR",
        },
    )
    exc2 = client.post(
        "/exceptions",
        json={
            "origen": "validation",
            "tipo_error": "ruc_invalido",
            "mensaje": "RUC inválido",
        },
    ).json()
    client.post(
        "/exceptions",
        json={
            "origen": "erp-connector",
            "tipo_error": "odoo_error",
            "mensaje": "Odoo inaccesible",
        },
    )

    # Resolver la segunda excepción
    client.patch(
        f"/exceptions/{exc2['id']}/resolver",
        json={"nota": "Proveedor corregido manualmente"},
    )

    # 1. Sin filtros: debe traer las 3
    res_all = client.get("/exceptions")
    assert res_all.status_code == 200
    assert len(res_all.json()) == 3

    # 2. Filtrar por estado pendiente: debe traer 2
    res_pendientes = client.get("/exceptions?estado=pendiente")
    assert res_pendientes.status_code == 200
    items_pendientes = res_pendientes.json()
    assert len(items_pendientes) == 2
    assert all(item["estado"] == "pendiente" for item in items_pendientes)

    # 3. Filtrar por estado resuelta: debe traer 1
    res_resueltas = client.get("/exceptions?estado=resuelta")
    assert res_resueltas.status_code == 200
    items_resueltas = res_resueltas.json()
    assert len(items_resueltas) == 1
    assert items_resueltas[0]["id"] == exc2["id"]
    assert items_resueltas[0]["estado"] == "resuelta"

    # 4. Filtrar por origen validation
    res_origen = client.get("/exceptions?origen=validation")
    assert res_origen.status_code == 200
    assert len(res_origen.json()) == 1
    assert res_origen.json()[0]["origen"] == "validation"


def test_resolve_exception_flow(client: TestClient):
    """
    Verifica el flujo de resolución:
    - Marca como resuelta con nota opcional
    - Impide resolver dos veces devolviendo 400
    """
    created = client.post(
        "/exceptions",
        json={
            "origen": "erp-connector",
            "tipo_error": "odoo_post_failed",
            "mensaje": "Factura duplicada en Odoo",
        },
    ).json()
    exc_id = created["id"]

    # 1. Resolver por primera vez con nota
    res_resolve = client.patch(
        f"/exceptions/{exc_id}/resolver",
        json={"nota": "Se verificó en Odoo y se descartó duplicado"},
    )
    assert res_resolve.status_code == 200
    resolved_data = res_resolve.json()
    assert resolved_data["estado"] == "resuelta"
    assert (
        resolved_data["nota_resolucion"]
        == "Se verificó en Odoo y se descartó duplicado"
    )
    assert resolved_data["resolved_at"] is not None

    # 2. Intentar resolver por segunda vez: debe fallar con 400
    res_second_resolve = client.patch(
        f"/exceptions/{exc_id}/resolver",
        json={"nota": "Segundo intento"},
    )
    assert res_second_resolve.status_code == 400
    assert "ya fue resuelta" in res_second_resolve.json()["detail"]


def test_resolve_exception_without_note(client: TestClient):
    """Verifica resolver una excepción sin enviar cuerpo (nota opcional)."""
    created = client.post(
        "/exceptions",
        json={
            "origen": "extraction",
            "tipo_error": "formato_no_soportado",
            "mensaje": "Archivo no legible",
        },
    ).json()

    exc_id = created["id"]
    res = client.patch(f"/exceptions/{exc_id}/resolver")
    assert res.status_code == 200
    assert res.json()["estado"] == "resuelta"
    assert res.json()["nota_resolucion"] is None


def test_resolve_nonexistent_exception(client: TestClient):
    """Verifica que intentar resolver una excepción inexistente devuelva 404."""
    res = client.patch(
        "/exceptions/99999/resolver",
        json={"nota": "No existe"},
    )
    assert res.status_code == 404
