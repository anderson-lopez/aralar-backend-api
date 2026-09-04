# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este proyecto

**Aralar API** — backend Flask para gestión de menús digitales de restaurantes, multi-tenant y multi-idioma. Los editores crean *templates* (estructura), luego *menús* (instancias con datos reales), los traducen, y el sistema los publica automáticamente al público según disponibilidad (día/fecha/timezone). Incluye usuarios/roles/permisos (RBAC + JWT), notificaciones, uploads a S3/MinIO y un subsistema de traducción automática con proveedores intercambiables.

> Lee también `HISTORY.md` (bitácora de decisiones y convenciones del repo — al terminar trabajo significativo, agrega una entrada nueva arriba con fecha, sin borrar las anteriores).

## Comandos

```bash
# Levantar todo (API + Mongo; agrega nllb si I18N_PROVIDER=nllb)
docker-compose up --build -d
docker-compose exec api python scripts/migrate.py   # migraciones/índices
docker-compose exec api python scripts/seed.py      # datos iniciales (admin, permisos)

# Desarrollo local (sin Docker; requiere Mongo local y .env con MONGO_URI=mongodb://localhost:27017/aralar)
flask --app aralar.app run --debug

# Tests (pytest + mongomock, no necesita Mongo real)
.venv/Scripts/python.exe -m pytest -q               # suite completa con cobertura (~40s)
pytest -q --no-cov                                  # rápido sin cobertura (~12s)
pytest tests/test_menus_service.py -q --no-cov      # un archivo
pytest tests/test_i18n.py::test_translate -q --no-cov  # un test
```

- Swagger UI: `http://localhost:8000/api/docs/swagger-ui`
- Cobertura objetivo: ≥70% en `aralar/services/`, ≥60% en `aralar/api/`, ≥65% global.

## Arquitectura

Flask + flask-smorest (OpenAPI), MongoDB (pymongo), JWT (flask-jwt-extended). Capas estrictas:

```
aralar/api/<módulo>/blueprint.py   → endpoints + permisos (@require_permissions)
aralar/services/<módulo>_service.py → lógica de negocio
aralar/repositories/<módulo>_repo.py → acceso a Mongo
aralar/schemas/<módulo>_schemas.py  → validación Marshmallow
aralar/core/                        → security, storage (S3), i18n providers
```

Blueprints registrados en `aralar/api/routes.py` bajo `/api/{auth,users,roles,menus,menu-templates,uploads,i18n,catalogs,notifications}`. Config por env vars en `aralar/config.py`. Para agregar un endpoint: blueprint → registrar en `routes.py` → schema → service → repo.

### Dominio: Templates → Menús → Render

1. **Template** (`/api/menu-templates`): define secciones y campos; cada campo tiene flag `translatable`. Ciclo draft → published (publicar genera un nuevo doc con `{slug, version}` estables). Solo se edita en draft.
2. **Menú** (`/api/menus`): instancia de un template publicado. Sus datos viven separados:
   - `common` → campos **no traducibles** (precios, fechas, imágenes, `_id` de platos, alérgenos)
   - `locales.{locale}.data` → campos **traducibles** (nombres, títulos) + `locales.{locale}.meta` (`title`/`summary` para listados públicos)
3. **Publicación en dos niveles**: por locale (`POST /:id/publish/es-ES`) y global (`POST /:id/publish`, exige availability + ≥1 locale publicado).
4. **Render público** (`GET /menus/:id/render?locale=..&fallback=..&with_ui=1`): fusiona `common` + locale en `menus_service.py`.

**Reglas de merge (críticas, no revertir):**
- En `_deep_merge_sections`: si una clave existe en ambos lados, **gana `common`** sobre locale.
- Secciones repetibles (arrays) se fusionan **por `_id`**: el `_id` debe existir idéntico en `common` y en cada locale.
- `update_common` llama a `_strip_common_keys_from_locales`: toda clave presente en `common` se borra automáticamente de los locales.
- Detalle completo para consumidores: `FRONTEND_COMMON_VS_LOCALES.md`.

### Subsistema i18n (traducción automática)

Patrón Strategy en `aralar/core/i18n/providers.py`: interfaz `I18nProvider` con tres implementaciones seleccionadas por env `I18N_PROVIDER`:
- `deepl` — API DeepL (calidad premium, ~30 idiomas europeos, sin euskera)
- `google` — Google Translate v2 (100+ idiomas, detect robusto)
- `nllb` — microservicio local en `services/nllb/` (FastAPI + facebook/nllb-200-distilled-600M, sin costo por request; ideal dev/pruebas). `NLLBProvider` mapea códigos ISO 639-1 → NLLB (`es`→`spa_Latn`) en `LANG_MAP`; el microservicio corre como sidecar Docker (puerto 8001, health en `/api/v1/health`).

Flujo en `I18nService.translate_batch`: hash SHA1 (texto+idiomas+provider+versión de glosario) → caché Mongo `translations_cache` → miss va al provider. Glosarios por tenant en colección `glossaries` (pre-sustitución local + restauración post-traducción; versionados, el cambio de versión invalida caché). Los schemas de `i18n_schemas.py` validan idiomas **dinámicamente según el provider configurado** (`_DEEPL_*`, `_GOOGLE_LANGS`, `_NLLB_LANGS` deben mantenerse en sync con los providers).

### Subsistema de reseñas de Google

Mismo patrón Strategy en `aralar/core/reviews/providers.py`, seleccionado por env
`GOOGLE_REVIEWS_PROVIDER`: `manual` (alta desde el panel, default) o `scraper` (endpoint
interno de Google Maps `listugcposts` vía `requests`, **sin navegador**). Las APIs oficiales
no sirven: Places devuelve máx. 5 reseñas y prohíbe almacenarlas; Business Profile exige
solicitud de acceso manual. Ver `HISTORY.md` para el razonamiento completo.

Flujo: `scripts/sync_google_reviews.py` (cron diario) → provider → upsert idempotente por
`(tenant_id, provider, external_id)` → moderación automática (`rating >= 4`) → lo demás queda
`pending` para revisión humana. La landing consume `GET /api/google-reviews/public`.

**Invariantes (no revertir):** el sync **nunca lanza** (los fallos van en `errors` y los datos
previos sobreviven); una decisión humana (`moderation.auto == False`) **no la pisa el sync**;
todo el mapa de índices del JSON de Google vive **solo** en `_parse_review`.

### Permisos

Formato `recurso:acción` (ej. `menus:update`). Efectivos = `(permisos_de_roles + allow) − deny`. Se siembran en `scripts/seed.py`.

## Gotchas conocidos

- **Underscore vs guión**: el permiso es `menu_templates:*` (underscore); `menu-templates` es solo el prefijo URL.
- Anti-softlock en users (no revertir): nadie se auto-elimina/desactiva; el último admin activo no puede ser eliminado, desactivado ni perder el rol admin (`is_last_active_admin`).
- `POST /auth/login` valida solo longitud de password; `POST /users` y `/auth/register` validan fortaleza. Login con usuario sin roles → 403 `no_permissions` (distinto de 401).
- Tests: `auth_headers()` (conftest) da todos los permisos de `DEFAULT_PERMISSIONS` — si creas un permiso nuevo, agrégalo ahí. Usa las factories de `tests/factories.py` (`make_menu`, `seed_template`, …) en vez de dicts inline. Marca tests con `@pytest.mark.unit|integration|e2e`. `boto3` y `requests.post` (providers) van mockeados.
- `/render` no hace merge con el template: usa solo el contenido del menú.

## Índice de documentación

Referencia canónica numerada en `docs/` (`00`–`07`); material temático agrupado en subcarpetas.

| Tema | Archivo |
|---|---|
| Visión general, actores, módulos | `docs/00_OVERVIEW.md` |
| Auth y usuarios | `docs/01_AUTH_USERS.md` |
| Templates (ciclo de vida, estructura) | `docs/02_TEMPLATES.md` |
| Menús (flujos, publicación, availability) | `docs/03_MENUS.md` |
| Render público y fallback de idioma | `docs/04_PUBLIC_RENDER.md` |
| Notificaciones (referencia) | `docs/05_NOTIFICATIONS.md` |
| Servicios de soporte (uploads, i18n, catálogos) | `docs/06_SUPPORT_SERVICES.md` |
| Diagrama ER de colecciones MongoDB | `docs/07_ER_DIAGRAM.md` |
| Guías de frontend (incl. common vs locales) | `docs/frontend/` |
| Servicios de menú ("Otros servicios") | `docs/frontend/FRONTEND_MENU_SERVICES.md` |
| Reseñas de Google (landing) | `docs/frontend/FRONTEND_GOOGLE_REVIEWS.md` |
| Simulaciones paso a paso de menús | `docs/simulations/` |
| Traducción: comparativa providers + ejemplos | `docs/i18n/` |
| Notificaciones: guía API + resumen impl. | `docs/notifications/` |
| Bitácora del repo | `HISTORY.md` |
