# Historial — Backend (Aralar API)

> **Lectura obligatoria al inicio de una nueva sesión** (sea humana o agente).
> Resume las decisiones arquitectónicas vigentes, el estado del último
> trabajo y las convenciones del repo. Si añades trabajo, agrega una entrada
> NUEVA arriba con fecha. **No borres las anteriores.**

---

## Convenciones del repo

### Source y mirror
Este backend existe en **dos rutas** que deben mantenerse byte-idénticas:

- `C:\Users\Anderson\Desktop\aralar-backend-api\` ← source
- `C:\Users\Anderson\Desktop\ligthNetwork\aralarBackendApi\` ← mirror (el que despliega Render)

Cualquier cambio en uno debe propagarse al otro antes de commitear ambos.
Los commits suelen ser idénticos en mensaje pero los SHA diferirán (es ok).

### Tests
- **pytest + mongomock** (Mongo en memoria por test) + **pytest-cov**.
- Comando completo: `.venv/Scripts/python.exe -m pytest -q` (~40s).
- Rápido sin cobertura: `pytest -q --no-cov` (~12s).
- Cobertura objetivo: **≥70% en `aralar/services/`**, **≥60% en `aralar/api/`**, **≥65% global**.
- Markers: `@pytest.mark.unit | integration | e2e`. Úsalos siempre.
- Fixtures globales en `tests/conftest.py`: `app`, `client`, `db`, `auth_headers`.
- Factories en `tests/factories.py`: `make_menu`, `seed_menu`, `make_image`, `make_template`, `seed_template`. **Úsalas en vez de dicts inline.**

### Permisos (relevante para tests)
- `auth_headers()` por defecto da TODOS los permisos del sistema (`DEFAULT_PERMISSIONS` en `conftest.py`).
- Si añades un endpoint con un permiso nuevo (ej. `notifications:export`), agrégalo a `DEFAULT_PERMISSIONS`.
- **OJO con el guión vs underscore**: `menu_templates:*` (con underscore en el código y permisos), NO `menu-templates:*` (con guión, que es solo el URL prefix).

### Endpoints clave de auth (lo que esperan los tests)
- `POST /auth/login` valida **solo length** de password (no fortaleza).
- `POST /users` y `POST /auth/register` validan fortaleza (mayús/minús/número).
- Si `/auth/login` devuelve 403 con `error: no_permissions`, el usuario existe pero no tiene roles → frontend debe distinguir esto de 401.

### Reglas anti-softlock activas
Están en `aralar/services/users_service.py` y `aralar/api/users/blueprint.py`:

1. Nadie puede eliminarse ni desactivarse a sí mismo.
2. Nadie puede eliminar/desactivar al **último admin activo** (helper `is_last_active_admin`).
3. `update_user_roles` rechaza quitar `admin` al último admin activo.

**No revertir.** El frontend (admin) también lo bloquea visualmente.

### Reglas de merge `common ↔ locales`
En `menus_service._deep_merge_sections`:
- Cuando `common` tiene un valor no vacío en una clave, **gana common** sobre `locales`.
- Solo si `common` está vacío/None, `locales` rellena.
- Esto arregla un bug de "imagen vieja del locale pisa la imagen nueva del common" cuando un campo pasa de `translatable=true` a `false`.

`update_common` además llama a `_strip_common_keys_from_locales` para limpiar las claves que ya viven en `common` de los `locales.<lang>.data`.

---

## Cambios por sesión

### 2026-08-05 — Fix: un menú ya no puede nacer `published`

Detectado al reproducir un reporte de QA (que en realidad probaba contra una imagen
anterior al fix del 500). `MenuCreateSchema` aceptaba `status` y `create` lo persistía
tal cual, así que un `POST /api/menus` con `"status": "published"` **entraba al listado
público sin pasar por `validate_menu`** — sin availability y sin ningún locale publicado.

`status` fuera del schema (→ **422**) y `create` fuerza `"draft"` siempre, para que la
invariante valga también en llamadas directas al service. Publicar sigue teniendo su
endpoint (`POST /:id/publish`), que sí valida. Mismo patrón que la identidad inmutable de
templates (2026-07-19). Ningún test existente se rompió: la suite ya asumía la regla.

### 2026-08-04 — Fix: 500 en `/render` y `locale_used` inventado en el listado público

Reportado por QA: `/public/available` listaba bien, pero al entrar al menú con el
`locale_used` que devolvía el propio listado, `/render` respondía **500**. Reproducido
antes de tocar nada. Eran **tres defectos encadenados**:

**1. `_merge_menu` devolvía dos formas incompatibles.** Si el menú no tenía bloque para
ese locale hacía `return common` (dict plano); si lo tenía, `{"data":…, "meta":…}`. Y
`render`/`render_featured_menus` hacen `result["data"]` sin comprobar → `KeyError` → 500.
Ahora **siempre** devuelve `{"data", "meta"}`.

**2. `effective_locale` mentía.** Su último recurso era `return locale`: si el menú no
tenía ningún idioma publicado, devolvía **el que le habías pedido**. Por eso en el
reporte había menús con `locale_used: "fr"` sin francés publicado. El frontend lo usaba
tal cual y recibía 409. Ahora devuelve `None` y el listado **omite** esos menús: sin
idioma publicado no hay nada que mostrar ni forma de renderizarlo.

**3. `publish_locale` permitía publicar un idioma sin contenido** — el habilitador que
creaba el dato malo. Ahora exige `locales.{locale}` con `data` o `meta`, y devuelve
**409** si no lo hay.

**No fue culpa del cambio de "listar siempre aunque falte el idioma"**: el defecto 1 era
anterior y estaba latente. Ese cambio solo lo **expuso**, al dejar de filtrar menús que
antes nunca llegaban a `/render`.

**Compatibilidad con datos ya existentes:** los menús rotos siguen en las bases de datos
y **no hay migración**. El fix 1 hace que se rendericen (devuelven `common` y `meta: {}`)
en vez de reventar; el fix 3 impide crear nuevos. Hay test explícito para ese caso
(`TestRenderOnLegacyBrokenData`).

Regresión en `tests/test_menus_locale_regression.py` (19 tests), incluido el contrato
punta a punta: *todo `locale_used` que devuelve el listado debe funcionar en `/render`*.
Guía de verificación manual en `docs/QA_FIX_LOCALE_RENDER.md`. Suite: **456 passed**.

### 2026-07-26 — Reseñas de Google en la landing (`google_reviews`)

Nueva vertical para pintar las opiniones de Google en la landing: extracción,
moderación, endpoints y job de sincronización.

**Por qué NO se usó ninguna API oficial** (investigado, no asumido):
- **Places API**: devuelve **máximo 5 reseñas**, no elegibles y sin paginación. Además
  los ToS de Maps §3.2.3(b) prohíben *"copy and save … user reviews"*, que es
  exactamente lo que pide el caso de uso. Inservible.
- **Business Profile API** (`mybusiness.googleapis.com/v4`): sí devuelve todas, pero
  exige solicitud de acceso manual (14 días según la FAQ de Google) + OAuth con
  refresh token del dueño. Habría bloqueado el desarrollo semanas.
- **Proveedores de pago** (SerpApi, Outscraper, ReviewHook): descartados por decisión
  explícita del cliente — sin API keys de terceros ni suscripciones.

**Decisión: scraping del endpoint interno de Maps, sin navegador.** Se descartó la
propuesta inicial de un microservicio Playwright: el DOM de Maps usa clases CSS
ofuscadas que Google rota (lo más frágil posible) y la imagen con Chromium pesa ~1.5 GB
para un job de 30 s al día. Con HTTP directo **no hizo falta contenedor nuevo, ni
Playwright, ni scheduler, ni una sola dependencia nueva** (`requests` ya estaba).

**⚠️ El endpoint correcto es `GetLocalBoqProxy`, NO `listugcposts`.** Se implementó
primero contra `listugcposts` (que es lo que documenta casi todo internet) y **responde
403**: está descontinuado. El que funciona hoy, verificado contra el local real:

```
GET /httpservice/web/PrivateLocalSearchUiDataService/GetLocalBoqProxy?msc=gwsrpc&reqpld=<json>
```

`reqpld` es un JSON anidado (no el `pb` de protobuf-en-texto del endpoint viejo) y su
forma **cambia entre la primera página y las siguientes**: en la primera el tamaño de
página va en la posición 9; en las demás el token de paginación va en la 19.

> ⚠️ El scraping incumple los ToS de Google. A 1 sincronización diaria de un solo local
> el riesgo práctico es bloqueo de IP, no acción legal. Decisión tomada por el cliente.

**Invariantes del diseño (no revertir):**
- **El sync nunca lanza.** `GoogleReviewsService.sync` captura todo y devuelve el fallo
  en `errors`. Si Google cambia el formato o bloquea, los datos ya guardados quedan
  intactos y `/public` sigue sirviendo el último estado bueno. La landing no se cae.
- **La decisión humana gana.** El upsert refresca contenido pero **no pisa `status` si
  `moderation.auto == False`**. Una reseña rechazada a mano no puede volver sola.
- **Clave de deduplicación = `external_id`**, no autor+fecha. La spec original proponía
  autor+fecha, pero la fecha del scraping es relativa (*"hace 3 semanas"*) y **cambia
  sola**: la misma reseña habría generado un documento nuevo en cada sync.
- **Todo el mapa de índices vive en `_parse_review`.** La respuesta son arrays
  posicionales; el acceso va por `_dig()` (tolerante) y, si un campo no está donde se
  espera, cae a búsqueda por señal (URL de avatar, entero 1-5, epoch). Un
  reordenamiento parcial degrada el dato pero no rompe la extracción.
- **Sin texto → `rejected`, no `pending`.** Medido sobre las 590 reseñas reales del
  local: **259 (44%) son solo estrellas, sin comentario**. Mandarlas a `pending`
  habría llenado la bandeja de moderación de items que nunca se podrían publicar
  (no hay tarjeta que pintar). Se rechazan solas pero se guardan y son recuperables.
  Así `pending` conserva su significado: *"tiene texto pero pocas estrellas, decide
  un humano"* — 22 items en vez de 103.
- **Orden público en Python, no en Mongo** (`_public_sort_key`): un `sort` ascendente en
  Mongo pone los `null` primero y queremos justo lo contrario. Mismo criterio que
  `_list_sort_key` de `menus_service.py`.

**Moderación:** umbral por estrellas (`rating >= 4`, configurable) + revisión humana de
lo que queda en `pending`. Sin modelo de ML: se evaluó y se descartó por ahora (nota:
**Perspective API está discontinuada**, fin de servicio 31-dic-2026).

**Mapa de índices, verificado contra el local real (2026-07-26).** Cada reseña es un
nodo de 48 campos dentro de `data[1][10][2]`; el token de la página siguiente está en
`data[1][10][6]`:

| Índice | Contenido |
|---|---|
| `r[1]` | valoración 1-5 (`r[45]` la repite; `r[46]` es siempre 5 = máximo) |
| `r[2][0]` / `r[2][2]` | fecha relativa / **epoch en ms como cadena** |
| `r[3][0..2]` | autor: nombre, foto, URL de perfil |
| `r[5]` | id estable de la reseña → `external_id` |
| `r[26]` | idioma |
| `r[27]` | **texto completo** (`r[28]` es un preview truncado — no usar) |

Si Google lo cambia, `scripts/sync_google_reviews.py --dump-raw <archivo>` guarda la
respuesta cruda y se toca **solo** `_parse_review` y el fixture
`tests/fixtures/google_reviews_response.json`.

**Verificado end-to-end:** 590 reseñas extraídas del local real, 100% con nombre, foto y
fecha, 590 ids únicos (sin duplicados). `GOOGLE_REVIEWS_MAX_PAGES` controla la
profundidad (~19 reseñas por página).

**Carga inicial automática, sin cron.** `docker-start.bat` / `.sh` / `make docker-init`
llaman a `sync_google_reviews.py --if-empty` después de migrar y sembrar. El flag es lo
que hace viable llamarlo en cada arranque: si el tenant ya tiene reseñas no consulta a
Google, así que levantar Docker 20 veces no son 20 scrapes. **Un fallo del sync nunca
aborta el arranque**: los scripts lo capturan y siguen (verificado ejecutándolos con
Docker apagado). Se descartó hacerlo dentro de Flask: `gunicorn.conf.py` tiene
`workers = 2`, así que un hook de arranque correría **dos veces en paralelo**.

Migraciones **016** (colección + índice único `(tenant_id, provider, external_id)`) y
**017** (permisos `google_reviews:*`). Doc de frontend en
`docs/frontend/FRONTEND_GOOGLE_REVIEWS.md`. Suite: **425 passed** (335 → 425).

### 2026-07-19 — Identidad inmutable en templates + menús solo sobre plantillas publicadas

Al revisar el bug del slug en `menu_services` se detectó **el mismo patrón, ya
existente, en `menu_templates`**. Verificado ejecutándolo, no deducido.

**El bug (antes del fix):** `MenuTemplateUpdateSchema` heredaba entero de
`MenuTemplateCreateSchema`, así que el `PUT` aceptaba `slug`. Al renombrar el slug
de un draft, los menús que apuntaban a `(template_slug, template_version)` quedaban
huérfanos, con dos consecuencias **silenciosas**:

1. `/render?include_ui=true` → `get_by_slug_version` devuelve `None`, hay un
   `if tmpl:` que omite el bloque → responde **200 sin `ui`**. El frontend pierde
   `layout`, orden de secciones y `catalogs` (alérgenos, currency) sin ningún error.
   Pasa desapercibido porque `/render` no mergea con el template.
2. `delete_template` cuenta menús con `count_by_template(t["slug"], t["version"])`,
   o sea el slug **actual** → tras el rename cuenta 0 → **deja borrar una plantilla
   en uso**. Comprobado: template borrado, menú vivo apuntando al vacío.

> El propio test `test_updates_draft_template_successfully` mandaba
> `slug: "any-slug"` sobre un template sembrado como `test-template`: estaba
> renombrando el slug como efecto colateral y nadie lo notó.

**Fixes (no revertir):**
- `MenuTemplateUpdateSchema` **ya no hereda de Create**. Solo acepta `name`,
  `i18n`, `sections`, `ui`. `slug`, `version`, `tenant_id` y `status` son identidad
  → **422**. (`status` además tiene sus propios endpoints publish/unpublish/archive.)
- `MenuTemplatesService._IMMUTABLE_FIELDS` + filtrado en `update_draft`: la
  invariante se cumple también para llamadas directas al service, no solo por HTTP.
  **Esto es lo que cierra la ruta adversarial**: `unpublish()` devuelve un template
  a `draft` y reabriría la ventana de edición, así que la protección no podía
  depender del estado.
- `MenusService.create` **exige `status == "published"`** en la plantilla
  (→ 400 `template is not published`). Antes se podía instanciar un menú sobre un
  draft —pese a lo que dice CLAUDE.md—, que es justo el estado en que la plantilla
  aún se puede editar. Cierra la exposición de raíz.

**Por qué el modelo usa `(slug, version)` y no `template_id`** (para futuras
sesiones): `publish()` sobre un template ya publicado **no muta**, hace `deepcopy` +
`insert` con `version+1`, así que **cada versión es un documento con su propio
`_id`**. El `_id` identifica *una versión*; el `slug` identifica *el linaje* a
través de versiones. Guardar el par hace el menú autodescriptivo (sin joins),
permite consultar por familia con índice (`004`: `[("template_slug",1),
("template_version",1)]`) y migrar de versión cambiando un entero. El `_id` habría
sido inmune al rename, pero opaco y atado a una versión. La decisión era correcta;
lo que faltaba era **hacer cumplir la inmutabilidad del slug** — eso es lo que se
arregla aquí.

**Tests añadidos:** `TestUpdateDraft::test_ignores_identity_fields` y
`::test_slug_stays_immutable_after_unpublish` (service),
`TestUpdateTemplate::test_rejects_identity_fields` (e2e, parametrizado sobre
slug/version/tenant_id/status), `TestCreateRequiresPublishedTemplate` (4 casos:
published OK, draft/archived rechazados, inexistente → None). **335 passed.**

### 2026-07-19 — Clasificación de menús por "Servicios" (sección "Otros servicios")

Requerimiento: la landing tendrá una sección **"Otros servicios"** que lista menús
clasificados por servicio (al inicio Desayunos, Lunch, Comida para llevar; a futuro
más). Esos menús **no** deben salir en `/public/available` — son dos lugares aparte.
Los servicios deben poder crearse/gestionarse por API y llevar nombre traducible.

**Decisiones de diseño (confirmadas con el cliente):**
- **Colección nueva `menu_services`** (CRUD), no un enum fijo: los servicios se crean,
  se traducen (`labels` i18n) y se ordenan (`order`).
- Un menú puede pertenecer a **varios** servicios → campo **`service_slugs: [str]`**
  (default `[]`). Vacío = menú normal.
- Dentro de un servicio se devuelven **tarjetas ligeras** (como `/public/available`;
  el front pide luego `/render`).

**Vertical nueva `menu_services`** (patrón roles/notifications):
`repositories/menu_services_repo.py`, `services/menu_services_service.py`,
`schemas/menu_service_schemas.py`, `api/menu_services/blueprint.py`
(prefijo URL `/api/menu-services`), registrada en `api/routes.py`. Permisos
`menu_services:{read,create,update,delete}` en `catalog/role_catalog.py`
(admin todos; manager read/create/update). Documento: `{tenant_id, slug, name,
labels, order, is_active}`; **slug único por tenant**.

**Endpoints menu_services:** `POST/GET/PUT/DELETE /api/menu-services` (auth),
`GET /api/menu-services/public` (público, solo activos, ordenado por `order`, alimenta
la sección). `DELETE` bloquea con **409** si algún menú referencia el servicio.

**Integración en menús (no revertir):**
- `service_slugs` se persiste en `create`, se edita con **`PUT /api/menus/<id>/general`**
  (whitelist ampliado) y se hereda en `duplicate` (es identidad, no posición).
- **Validación**: al asignar, cada slug debe existir y estar activo para el tenant
  (`MenusService._resolve_service_slugs`, con `MenuServicesRepo` inyectado en el
  constructor como 3er arg opcional). Slug desconocido/inactivo → **400**.
- **Exclusión**: `menus_repo.list_published_by_day` ahora filtra `service_slugs`
  vacío/ausente → los clasificados NO salen en `/public/available`.
- **Listado por servicio**: `menus_repo.list_service_menus_by_day` (equality sobre
  el array) + `MenusService.service_menus_on/now`, reutilizando `_list_sort_key`
  (mismo orden que el listado general). Ruta pública nueva
  **`GET /api/menus/public/services/<slug>`** (tarjetas ligeras, reusa `_public_item`).
- `MenuSchema` y `MenuPublicItemSchema` exponen `service_slugs`.

**Migraciones:** `014_create_menu_services_collection.py` (índices, siembra los 3
servicios por defecto si vacío, normaliza menús existentes a `service_slugs: []`),
`015_sync_menu_services_permissions.py` (`apply_catalog` + descripciones).

> **`/public/featured` no se tocó a propósito**: un menú podría ser featured y estar
> en un servicio; la landing de destacados es un circuito aparte.

**El `slug` de un servicio es INMUTABLE (no revertir).** Los menús lo referencian
como texto en `service_slugs`, sin cascada: renombrarlo dejaría esos menús
**huérfanos** (fuera de `/public/available` por estar clasificados, y fuera de
`/public/services/<slug>` por no coincidir), y en silencio. Por eso `slug` no está
en `MenuServiceUpdateSchema` → mandarlo da **422**. Lo visible (`labels`/`name`) sí
se edita. Para cambiar de slug: crear servicio nuevo, reasignar, borrar el viejo.

**Desactivar** (`is_active: False`) sí se permite (apagar temporalmente es legítimo),
pero oculta los menús del servicio: la respuesta del `PUT` incluye **`affected_menus`**
con cuántos quedan ocultos para que el panel avise antes de confirmar.

**Documentación para frontend:** `docs/frontend/FRONTEND_MENU_SERVICES.md` (guía
completa: qué cambió, endpoints públicos y CRUD, propuesta de UI, casos borde,
tabla de errores). `FRONTEND_GUIDE.md` §3.5 queda como resumen que enlaza a ella.

**Tests añadidos:** `test_menu_services_service.py` (CRUD, slug único por tenant,
delete bloqueado, public_list), `test_menu_services_endpoints.py` (CRUD e2e, 401/403,
409, `/public`), en menús `TestServiceClassification` + `TestResolveServiceSlugs`
(exclusión, filtrado por servicio, validación, herencia en duplicado) y e2e
`TestPublicServiceMenus` + `TestUpdateGeneralServiceSlugs`; `expected_keys` incluye
`service_slugs`; slug inmutable (422 en HTTP, ignorado en el service) y aviso
`affected_menus` al desactivar. **325 passed.**

### 2026-07-18 — Orden manual del listado público (`list_order`)

Requerimiento: el cliente necesita controlar **en qué orden salen los menús** en la
sección "Listas de Menús" (que el frontend alimenta con `/api/menus/public/available`).

**Hallazgo de la indagación:** ya existía `featured_order`, pero está cableado
**solo** a `/public/featured` (landing con menús pre-renderizados). El
`/public/available` ordenaba únicamente por `updated_at` desc, sin prioridad manual.
Se descartó reusar `featured_order` porque obligaría a marcar `featured=True` y
mezclaría dos conceptos hoy separados.

**Campo nuevo: `list_order`** (entero, nullable, default `None`).
- Convención **menor = más prioritario** (igual que `featured_order`, por coherencia).
- Se edita con el endpoint existente **`PUT /api/menus/<id>/general`** (permiso
  `menus:update`); no hizo falta endpoint ni permiso nuevo.
- Se expone en `MenuSchema` y en cada item de `/public/available`.
- `duplicate` lo resetea a `None` (la copia no hereda la posición del original).

**Orden aplicado (no revertir):** `list_order` asc → los `None` **al final** →
empate por `updated_at` desc. Implementado en `MenusService._list_sort_key` y
aplicado en `available_on`.

> **Por qué el sort va en Python y no en Mongo:** un `sort` ascendente en Mongo pone
> los `null` **primero**, justo lo contrario de lo requerido. Como
> `list_published_by_day` devuelve el set completo del día (sin paginar), ordenar en
> el service es determinista y barato. `0` y los negativos son valores válidos y se
> distinguen correctamente de "sin orden".

> **Bug latente detectado (no tocado):** `list_featured_by_day` comenta "nulls last"
> pero usa `.sort([("featured_order", 1), ...])`, así que en Mongo los `featured_order`
> nulos salen **primero**. Solo afecta a `/public/featured`. Pendiente si el cliente lo reporta.

**Archivos:** `schemas/menu_schemas.py` (`MenuCreateSchema`, `MenuGeneralUpdateSchema`,
`MenuSchema`, `MenuPublicItemSchema`), `services/menus_service.py` (`create`,
`duplicate`, `update_general`, `_list_sort_key`, `available_on`),
`api/menus/blueprint.py` (item del listado), `tests/factories.py` (`make_menu`).

**Tests añadidos:** `TestAvailableOnOrdering` (integration, 6: asc, nulls last,
desempate por recencia, sin ningún orden, `0` válido, negativos),
`TestUpdateGeneralListOrder` (e2e, 3: set, limpiar con null, no pisar si ausente),
1 e2e de orden en el listado, y `expected_keys` incluye `list_order`. **274 passed.**

### 2026-07-18 — Listado público independiente del idioma (`/public/available`)

Requerimiento del cliente: **los menús deben listarse siempre**, aunque el idioma
pedido no exista para ese menú (si no hay inglés, que salga el español/idioma por defecto).

**Causa raíz:** `list_published_by_day` gateaba por `publish.{locale}.status ==
"published"`, excluyendo del listado cualquier menú sin ese idioma exacto.

**Fix (no revertir):**
- `menus_repo.list_published_by_day`: **se quitó el filtro por locale**. Un menú con
  `status == "published"` ya tiene ≥1 locale publicado garantizado (`validate_menu`),
  así que el gate por idioma no es necesario para saber que hay contenido mostrable.
  La firma ya no recibe `locale`.
- `MenusService.effective_locale(menu, locale, fallback)` (nuevo): resuelve el idioma
  a mostrar con cascada **locale pedido → fallback explícito → primer locale publicado**
  (en la práctica el idioma por defecto, p.ej. es-ES). Solo cuenta locales publicados.
- `/public/available`: cada item ahora resuelve `title`/`summary` con el idioma efectivo
  y expone el nuevo campo **`locale_used`** (idioma real devuelto). El frontend debe
  usar `locale_used` para el `/render` posterior y evitar el 409 por locale ausente.

> **Ámbito:** solo `/public/available`. `/public/featured` (render completo para landing)
> mantiene su gate por locale/fallback a propósito — no se tocó.

**Archivos:** `repositories/menus_repo.py`, `services/menus_service.py`,
`api/menus/blueprint.py`, `schemas/menu_schemas.py` (`MenuPublicItemSchema.locale_used`).

**Tests añadidos/actualizados:** `TestEffectiveLocale` (unit, 4), 3 e2e en
`TestPublicAvailable` (locale ausente → default, locale presente, fallback explícito),
`available_on` ahora lista aunque falte el locale, y `expected_keys` incluye `locale_used`.

### 2026-07-18 — Endpoints de duplicación (menús y templates)

Nueva acción "duplicar" para reaprovechar contenido ya cargado, expuesta como
endpoint dedicado en cada recurso (no se reutiliza `create`).

**Endpoints nuevos:**
- `POST /api/menus/<id>/duplicate` — permiso `menus:create`. Body opcional `{name?}`.
- `POST /api/menu-templates/<id>/duplicate` — permiso `menu_templates:create`. Body opcional `{name?, slug?}`.

No hicieron falta permisos nuevos (duplicar = crear) → sin cambios en `seed.py`/`DEFAULT_PERMISSIONS`.

**Reglas de duplicación (no revertir):**
- **Menú** (`MenusService.duplicate`): copia `common`, `locales`, `availability` y la
  referencia al template; **resetea** `status=draft`, `publish={}`, `featured=False`,
  `featured_order=None`. Nombre por defecto `"<name> (copia)"`. Usa `deepcopy` (no comparte refs con el original).
- **Template** (`MenuTemplatesService.duplicate`): duplicar ≠ versionar. Copia
  `sections/ui/i18n`; **resetea** `status=draft`, `version=1`, limpia `publish_notes`.
  Slug derivado `"<slug>-copy"` con resolución de colisión (`-copy-2`, `-copy-3`, …)
  vía `_derive_copy_slug`. Slug explícito duplicado → `{"conflict": ...}` → 409.

**Archivos:** `services/menus_service.py`, `services/menu_templates_service.py`,
`api/menus/blueprint.py`, `api/menu_templates/blueprint.py`, `schemas/menu_schemas.py`
(`MenuDuplicateSchema`), `schemas/menu_template_schemas.py` (`MenuTemplateDuplicateSchema`).

**Tests añadidos:** `TestDuplicate` (menus service), `TestDuplicateTemplate` (templates
service), `TestDuplicateMenu` (menus e2e), `TestDuplicateTemplate` (templates e2e).

> Nota de entorno: en esta máquina (`c:\Users\PC\Documents\aralarBackendApi`) el `.venv`
> estaba vacío; hubo que reinstalar `requirements.txt` (Python 3.14) para correr la suite.

### 2026-05-28 → 2026-06-03 — Suite de tests + reglas anti-softlock + cleanup

**Tests añadidos** (`tests/`): **233 tests / 74% cobertura global** (`72%` services, `68%` api).

| Bloque | Archivos | Notas |
|---|---|---|
| A — Services | `test_menus_service.py`, `test_menu_templates_service.py`, `test_roles_service.py` | Pure-unit + integration con mongomock. |
| B — Endpoints | `test_menus_endpoints.py`, `test_menu_templates_endpoints.py` | E2E vía `client`. Happy + 400/401/403/404/409. |
| C — Auth/Permisos/Externos | `test_auth.py`, `test_permissions.py`, `test_users.py`, `test_notifications.py`, `test_uploads.py`, `test_i18n.py` | `boto3` y `requests.post` (DeepL/Google) mockeados. |

**Backend code changes:**
- `is_last_active_admin()` en `users_service.py` (cuenta admins activos en BD).
- Guards en `blueprint.py`: `delete_user`, `deactivate_user`, `update_user_roles`.
- `_deep_merge_sections` endurecido para que common gane sobre locales.
- `_strip_common_keys_from_locales` en `update_common`.

**Pendientes** (no scope de esta sesión):
- Subir `notifications_service.py` (61%), `token_blacklist_service.py` (43%), `uploads_service.py` (54%) si se quiere más cobertura.
- El `aralar/api/notifications/controllers.py` envuelve `abort(404)` del service en `try/except → abort(500)` (bug latente: el 404 del service se reporta como 500).

---

## Cómo verificar el estado en tu primera vuelta

```bash
cd C:\Users\Anderson\Desktop\ligthNetwork\aralarBackendApi
.venv/Scripts/python.exe -m pytest -q     # debe dar 233 passed
git status                                # debe estar limpio
git log -1 --oneline                      # último commit conocido en main
```

Si pytest no corre, falta `.venv`:
```bash
python -m venv .venv
.venv/Scripts/pip.exe install -r requirements.txt
```

El mirror (`aralar-backend-api`) debe quedar idéntico tras cualquier cambio.
