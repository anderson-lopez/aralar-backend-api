def init_api_docs(app):
    # flask-smorest usa config de app: API_TITLE, API_VERSION, OPENAPI_VERSION
    # Agrega /swagger-ui y /openapi.json automáticamente
    app.config["OPENAPI_URL_PREFIX"] = "/api/docs"
    app.config["OPENAPI_JSON_PATH"] = "openapi.json"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["OPENAPI_REDOC_PATH"] = "/redoc"
    app.config["OPENAPI_REDOC_URL"] = "https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"
    
    # Configurar JWT Bearer authentication para Swagger UI
    app.config["API_SPEC_OPTIONS"] = {
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT Bearer token authentication"
                }
            }
        }
    }
