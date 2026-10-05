def add_contract(result, generator, request, public):
    """Describe shared error/CSRF contracts alongside generated serializers."""
    result["components"]["schemas"]["ApiError"] = {
        "type": "object",
        "required": ["error"],
        "properties": {
            "error": {
                "type": "object",
                "required": ["code", "message", "fields"],
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "fields": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
        },
    }
    for path, operations in result["paths"].items():
        for method, operation in operations.items():
            if method not in {"get", "post", "patch"}:
                continue
            errors = {
                "400": "Validación o credenciales inválidas",
                "403": "Sin sesión, CSRF inválido o permiso insuficiente",
            }
            if "{workspace_id}" in path:
                errors["404"] = "Workspace no autorizado/inexistente o ficha ajena"
            for status, description in errors.items():
                operation["responses"][status] = {
                    "description": description,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ApiError"}
                        }
                    },
                }
            if method in {"post", "patch"}:
                operation.setdefault("parameters", []).append(
                    {
                        "name": "X-CSRFToken",
                        "in": "header",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Token obtenido en auth/csrf/; usar cookie del mismo origen.",
                    }
                )
            for parameter in operation.get("parameters", []):
                if parameter["in"] == "path":
                    parameter["schema"] = {"type": "string", "format": "uuid"}
    return result
