# Guía de tests — Aralar API

Esta guía explica **cómo está organizada la suite de tests** y **cómo escribir uno nuevo** paso a paso. Léela antes de tocar nada.

---

## 🚀 Correr los tests

```bash
# Todos los tests + reporte de cobertura en consola y htmlcov/
make test
# o directamente:
pytest

# Solo un archivo
pytest tests/test_menus_service.py

# Solo una clase
pytest tests/test_menus_service.py::TestExtractImageUrls

# Solo un test específico
pytest tests/test_menus_service.py::TestExtractImageUrls::test_returns_empty_list_when_menu_has_no_images

# Solo tests marcados como unitarios (rápido)
pytest -m unit

# Solo los que fallaron la última vez
pytest --lf
```

El reporte HTML de cobertura queda en `htmlcov/index.html` — ábrelo para ver qué líneas del código NO están cubiertas.

---

## 📁 Estructura

```
tests/
├── conftest.py                         ← fixtures globales (app, client, db, auth_headers)
├── factories.py                        ← helpers para construir datos de prueba
├── README.md                           ← este archivo
├── test_menus_service.py               ← unit + integration del service
├── test_menus_endpoints.py             ← E2E HTTP de endpoints de menús
├── test_menu_templates_service.py
├── test_menu_templates_endpoints.py
├── test_auth.py                        ← login, refresh, logout
├── test_permissions.py                 ← autorización, JWT, blacklist
├── test_users.py
├── test_notifications.py
├── test_uploads.py                     ← requiere mockear boto3
└── test_i18n.py                        ← requiere mockear requests
```

**Regla**: un archivo por módulo del código (`aralar/services/menus_service.py` → `tests/test_menus_service.py`). Si un archivo supera ~500 líneas, divide por funcionalidad.

---

## 🧪 Los 3 tipos de tests

| Tipo | Marker | Qué prueba | Velocidad | Cuándo usar |
|------|--------|------------|-----------|-------------|
| **Unit** | `@pytest.mark.unit` | Una función pura, sin Flask ni Mongo | ⚡⚡⚡ ms | Lógica determinística (cálculos, merges, validaciones) |
| **Integration** | `@pytest.mark.integration` | Service + Repo + mongomock | ⚡⚡ 10-100ms | Consultas a DB, queries complejas |
| **E2E** | `@pytest.mark.e2e` | HTTP request → toda la stack | ⚡ 100-500ms | Status codes, JSON, auth |

**Prefiere unit tests siempre que puedas** — son más rápidos, más precisos, y fallan con mensajes más claros.

---

## 🧰 Fixtures disponibles

Están todas en `conftest.py` y no requieren import.

### `app`
Instancia Flask con mongomock ya inyectado. Cada test recibe una app nueva.

### `client`
Test client HTTP. Usar para tests E2E.

```python
def test_returns_200(client):
    res = client.get("/api/menus/public/available?locale=es-ES&date=2025-09-27")
    assert res.status_code == 200
```

### `db`
Referencia directa a la DB mongomock. Usar para sembrar datos o verificar estado.

```python
def test_create_persists(client, db):
    client.post("/api/menus", json={...})
    assert db["menus"].count_documents({}) == 1
```

### `auth_headers` (factory)
Devuelve una **función** que crea un usuario en la DB y genera headers con JWT.

```python
def test_protected(client, auth_headers):
    # Usuario admin con todos los permisos
    res = client.get("/api/menus", headers=auth_headers())
    assert res.status_code == 200

def test_forbidden(client, auth_headers):
    # Usuario con permiso insuficiente
    headers = auth_headers(permissions=["other:perm"])
    res = client.post("/api/menus", json={...}, headers=headers)
    assert res.status_code == 403
```

---

## 🏭 Factories (`tests/factories.py`)

En vez de escribir dicts gigantes inline, usa los helpers:

| Factory | Qué hace |
|---------|----------|
| `make_menu(**overrides)` | Construye un dict de menú con defaults sensatos |
| `make_template(**overrides)` | Dict de template mínimo publicado |
| `make_image(url=..., mime=...)` | Dict de imagen `{url, mime, width, height, size}` |
| `seed_menu(db, **overrides)` | Inserta un menú en mongomock y devuelve con `_id` |
| `seed_template(db, **overrides)` | Inserta un template en mongomock |

```python
from tests.factories import seed_menu, make_image

def test_preview_images_from_banner(client, db):
    seed_menu(db, common={
        "header": {"banner_image": make_image(url="https://cdn/foo.webp")}
    })
    res = client.get("/api/menus/public/available?locale=es-ES&date=2025-09-27")
    assert res.json["items"][0]["preview_images"] == ["https://cdn/foo.webp"]
```

---

## ✍️ Cómo escribir un test nuevo — paso a paso

### 1. Identificar qué quiero probar

Ejemplo: "quiero probar que `MenusService.resolve_meta` usa el fallback locale cuando el locale principal no tiene la key".

### 2. Elegir tipo

`resolve_meta` es lógica pura → **unit test**. Va en `test_menus_service.py` dentro de `class TestResolveMeta`.

### 3. Nombrar el test

Formato: `test_<que>_<cuando>_<resultado>`.

✅ `test_resolve_meta_falls_back_to_fallback_locale_when_primary_missing_key`
❌ `test_fallback` (muy genérico, no dice nada)

### 4. Escribir siguiendo el patrón AAA (Arrange / Act / Assert)

```python
def test_resolve_meta_falls_back_to_fallback_locale_when_primary_missing_key(self):
    # Arrange — preparar el input
    menu = make_menu(locales={
        "es-ES": {"meta": {}},  # primary sin la key "title"
        "en-GB": {"meta": {"title": "English title"}},
    })

    # Act — ejecutar el método
    result = self.svc.resolve_meta(menu, "title", locale="es-ES", fallback="en-GB")

    # Assert — verificar UNA cosa
    assert result == "English title"
```

### 5. Correr y verificar

```bash
pytest tests/test_menus_service.py::TestResolveMeta::test_resolve_meta_falls_back_to_fallback_locale_when_primary_missing_key -v
```

---

## 📜 Reglas de oro (claras esta vez)

1. **Un test = un escenario**. No pongas 5 `assert` validando cosas distintas. Si un test falla, debe haber UNA razón obvia.

2. **Tests independientes**. Cada test crea sus propios datos. Si corres los tests en orden aleatorio (`pytest -p no:cacheprovider --randomly`), todos siguen pasando.

3. **Mockea solo lo externo**. Mockea S3 (boto3), DeepL/Google (requests), correos. **NO mockees el método que estás probando**, ni el service cuando pruebas el endpoint.

4. **Mongo → usa mongomock, NO lo mockees**. Ya está parcheado automáticamente en `conftest.py`. Siempre que puedas, deja correr la query real contra mongomock en vez de mockear el repo.

5. **Nombres descriptivos**. `test_returns_401_without_token` > `test_auth_1`.

6. **Copia el patrón de los ejemplos existentes**:
   - Unit test → `TestExtractImageUrls` en `test_menus_service.py`
   - E2E test → `TestPublicAvailable` en `test_menus_endpoints.py`

---

## 🎯 Meta de cobertura

- `aralar/services/` → **≥ 70%**
- `aralar/api/` → **≥ 60%**
- Global → **≥ 65%**

Verifica con:

```bash
pytest --cov=aralar --cov-report=term-missing
```

Abre `htmlcov/index.html` para ver visualmente qué líneas faltan.

---

## 🆘 Troubleshooting

### El test de E2E devuelve 429 (rate limit)
El rate limiter ya está desactivado en `conftest.py`. Si pasa, verifica que tu fixture use `app` (no cree una propia).

### El test de E2E devuelve 401 aunque mando el token
Revisa el blueprint: probablemente usa `@require_permissions("X:Y")`. Genera el token con ese permiso:

```python
auth_headers(permissions=["X:Y"])
```

### El test no encuentra datos sembrados
¿Usaste `seed_menu(db, ...)`? ¿Los filtros del endpoint (availability, locale, status) coinciden con lo que sembraste? Los defaults de `seed_menu` son amplios (todos los días, rango 2020→2099, publicado en es-ES).

### `make test` falla con "module not found"
```bash
pip install -r requirements.txt
```

### Un test falla solo cuando se corre con otros, pero pasa aislado
Estado compartido entre tests. Alguno no está limpiando. Revisa si alguien usa variables globales o fixtures con `scope="session"` que deberían ser `function`.

---

## 📚 Referencias

- [pytest docs](https://docs.pytest.org/en/stable/)
- [Flask testing](https://flask.palletsprojects.com/en/3.0.x/testing/)
- [mongomock](https://github.com/mongomock/mongomock)
- [flask-jwt-extended testing](https://flask-jwt-extended.readthedocs.io/)

---

## ✅ Checklist antes de hacer PR

- [ ] `make test` pasa verde
- [ ] Cobertura del módulo tocado ≥ 70%
- [ ] Cada test tiene nombre descriptivo (`test_<que>_<cuando>_<resultado>`)
- [ ] Cada test valida **una** cosa
- [ ] Usé factories en vez de dicts gigantes
- [ ] No hay `print()` ni tests comentados
- [ ] Agregué docstring a nuevas clases `TestXxx` explicando qué cubren
