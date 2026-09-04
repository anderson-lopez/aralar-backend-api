# Guía de verificación — Fix del 500 en `/render` y del `locale_used` inventado

Guion completo para validar a mano los tres arreglos del reporte *"los menús se listan
pero al entrar dan 500"*. **Parte de una base de datos vacía**: incluye la creación de la
plantilla y los menús necesarios.

Referencia de payloads más completos: `docs/simulations/MENU_SIMULATION_DAILY_BASIC.md`.

---

## Índice

1. [Preparación del entorno](#1-preparación-del-entorno)
2. [Crear la plantilla](#2-crear-la-plantilla)
3. [Crear el menú bueno](#3-crear-el-menú-bueno-menú-a)
4. [Inyectar los menús rotos](#4-inyectar-los-menús-rotos-datos-pre-fix)
5. [Casos de prueba](#5-casos-de-prueba)
6. [Limpieza](#6-limpieza)

---

## 1. Preparación del entorno

```bash
docker-compose up --build -d      # imprescindible reconstruir: hay cambios de código
docker-compose exec api python scripts/migrate.py
docker-compose exec api python scripts/seed.py
```

No hay migración nueva para este fix. Los datos viejos se siguen leyendo, solo dejan de
romper — **no hace falta borrar nada**.

### Obtener el token

```bash
curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@aralar.local","password":"ChangeMeNow!2025"}'
```

Guarda el `access_token` en una variable:

```bash
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@aralar.local","password":"ChangeMeNow!2025"}' | jq -r '.access_token')
echo $TOKEN
```

> Si cambiaste `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` en el `.env`, usa esos valores.

---

## 2. Crear la plantilla

Plantilla mínima: una sola sección con un campo traducible. Suficiente para el fix.

```bash
curl -s -X POST "http://localhost:8000/api/menu-templates" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "name": "QA Fix Locale",
    "slug": "qa-fix-locale",
    "tenant_id": "aralar",
    "version": 1,
    "status": "draft",
    "sections": [
      {
        "key": "header",
        "label": { "es-ES": "Cabecera", "en-GB": "Header" },
        "repeatable": false,
        "fields": [
          { "key": "title", "type": "text", "required": true, "translatable": true }
        ],
        "ui": { "role": "header", "order": 0, "display": "hero" }
      }
    ],
    "ui": { "layout": "sections", "catalogs": {} }
  }'
```

Devuelve `{"id": "..."}`. Guárdalo y **publica la plantilla** (un menú solo se puede crear
sobre una plantilla publicada):

```bash
TPL=<id_devuelto>
curl -s -X POST "http://localhost:8000/api/menu-templates/$TPL/publish" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"notes":"v1 para QA"}'
```

---

## 3. Crear el menú bueno (Menú A)

Es el menú correcto: sirve de control para comprobar que **no se rompió el flujo normal**.

### 3.1 Crear

```bash
curl -s -X POST "http://localhost:8000/api/menus" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "aralar",
    "name": "Menu A (bueno)",
    "template_slug": "qa-fix-locale",
    "template_version": 1,
    "status": "draft",
    "common": {}
  }'
```

Guarda el `_id`: `MENU_A=<id>`

### 3.2 Disponibilidad

**El rango debe incluir la fecha de hoy** o el menú no saldrá en el listado público.

```bash
curl -s -X PUT "http://localhost:8000/api/menus/$MENU_A/availability" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "timezone": "Europe/Madrid",
    "days_of_week": ["MON","TUE","WED","THU","FRI","SAT","SUN"],
    "date_ranges": [{ "start": "2026-01-01", "end": "2027-12-31" }]
  }'
```

### 3.3 Contenido en es-ES

```bash
curl -s -X PUT "http://localhost:8000/api/menus/$MENU_A/locales/es-ES" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "data": { "header": { "title": "Menú del día" } },
    "meta": { "title": "Menú del día", "summary": "Prueba QA" }
  }'
```

### 3.4 Publicar el idioma y el menú

```bash
curl -s -X POST "http://localhost:8000/api/menus/$MENU_A/publish/es-ES" \
  -H "Authorization: Bearer $TOKEN"

curl -s -X POST "http://localhost:8000/api/menus/$MENU_A/publish" \
  -H "Authorization: Bearer $TOKEN"
```

Ambos deben devolver `{"message": "ok"}`.

### 3.5 Comprobación rápida

```bash
curl -s "http://localhost:8000/api/menus/public/available?locale=es-ES" | jq '.items'
```

Debe aparecer **Menú A** con `"locale_used": "es-ES"` y `"title": "Menú del día"`.

---

## 4. Inyectar los menús rotos (datos pre-fix)

Los menús rotos **ya no se pueden crear por la API** — eso es precisamente el fix 3. Para
reproducir el escenario de QA hay que insertarlos directamente en Mongo, simulando datos
creados antes del arreglo.

```bash
docker-compose exec mongo mongosh aralar --quiet --eval '
db.menus.insertMany([
  {
    tenant_id: "aralar",
    name: "Menu B (roto: idioma publicado sin contenido)",
    template_slug: "qa-fix-locale",
    template_version: 1,
    status: "published",
    common: { header: { title: "Contenido comun" } },
    locales: {},                                              // <-- sin bloque de idioma
    publish: { "es-ES": { status: "published", published_at: "2026-08-04T00:00:00Z" } },
    availability: {
      timezone: "Europe/Madrid",
      days_of_week: ["MON","TUE","WED","THU","FRI","SAT","SUN"],
      date_ranges: [{ start: "2026-01-01", end: "2027-12-31" }]
    },
    service_slugs: [], list_order: null, featured: false,
    updated_at: new Date()
  },
  {
    tenant_id: "aralar",
    name: "Menu C (roto: ningun idioma publicado)",
    template_slug: "qa-fix-locale",
    template_version: 1,
    status: "published",
    common: {},
    locales: {},
    publish: {},                                              // <-- nada publicado
    availability: {
      timezone: "Europe/Madrid",
      days_of_week: ["MON","TUE","WED","THU","FRI","SAT","SUN"],
      date_ranges: [{ start: "2026-01-01", end: "2027-12-31" }]
    },
    service_slugs: [], list_order: null, featured: false,
    updated_at: new Date()
  }
]);
db.menus.find({}, {name:1, publish:1, locales:1}).forEach(printjson);
'
```

Apunta los ids que devuelve: `MENU_B` y `MENU_C`.

---

## 5. Casos de prueba

### Caso 1 — El bug original ya no revienta ⭐

```bash
curl -i "http://localhost:8000/api/menus/$MENU_B/render?locale=es-ES"
```

| Antes | Ahora |
|---|---|
| `500 Internal Server Error` (HTML) | **`200 OK`** con JSON |

El JSON trae `data` con el contenido de `common` y `meta: {}`. Que `meta` venga vacío es
correcto: ese menú nunca tuvo contenido en su idioma.

✅ **Pasa si:** devuelve 200 y no un HTML de error.

---

### Caso 2 — El listado ya no inventa idiomas

```bash
curl -s "http://localhost:8000/api/menus/public/available?locale=fr" \
  | jq '.items[] | {name, locale_used}'
```

| Menú | Resultado esperado |
|---|---|
| **A** (publicado en es-ES) | `"locale_used": "es-ES"` ← cae a su idioma real |
| **B** (idioma publicado sin contenido) | `"locale_used": "es-ES"` |
| **C** (sin ningún idioma publicado) | **no aparece** |

✅ **Pasa si:** ningún item devuelve `locale_used: "fr"`, y **Menú C no está en la lista**.

Antes del fix, B y C devolvían `"locale_used": "fr"` sin tener francés publicado.

---

### Caso 3 — El contrato completo ⭐⭐ *(la prueba que de verdad valida el fix)*

Valida lo que se documentó al frontend: *"usa `locale_used` para llamar a `/render`"*.
Recorre el listado y renderiza cada menú con el idioma que el propio listado devolvió.

```bash
for row in $(curl -s "http://localhost:8000/api/menus/public/available?locale=fr" \
             | jq -r '.items[] | "\(.id):\(.locale_used)"'); do
  id="${row%%:*}"; loc="${row##*:}"
  code=$(curl -s -o /dev/null -w "%{http_code}" \
         "http://localhost:8000/api/menus/$id/render?locale=$loc")
  echo "$code  $id  locale=$loc"
done
```

PowerShell:

```powershell
$items = (Invoke-RestMethod "http://localhost:8000/api/menus/public/available?locale=fr").items
foreach ($i in $items) {
  $r = Invoke-WebRequest "http://localhost:8000/api/menus/$($i.id)/render?locale=$($i.locale_used)" -SkipHttpErrorCheck
  "$($r.StatusCode)  $($i.name)  locale=$($i.locale_used)"
}
```

✅ **Pasa si:** **todas** las líneas dicen `200`. Cualquier `409` o `500` es un fallo.

---

### Caso 4 — Ya no se puede crear el dato malo

Esta es la causa raíz: antes se podía publicar un idioma **sin haberle cargado contenido**,
y así nacía el menú roto.

**4.a — Publicar un idioma vacío debe fallar**

```bash
curl -i -X POST "http://localhost:8000/api/menus/$MENU_A/publish/fr" \
  -H "Authorization: Bearer $TOKEN"
```

| Antes | Ahora |
|---|---|
| `200 OK` (creaba el menú roto) | **`409 Conflict`** — `locale 'fr' has no content to publish` |

✅ **Pasa si:** devuelve 409.

**4.b — Con contenido sí publica**

```bash
curl -s -X PUT "http://localhost:8000/api/menus/$MENU_A/locales/fr" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"data": {"header": {"title": "Menu du jour"}}, "meta": {"title": "Menu du jour"}}'

curl -i -X POST "http://localhost:8000/api/menus/$MENU_A/publish/fr" \
  -H "Authorization: Bearer $TOKEN"
```

✅ **Pasa si:** devuelve `200 OK`.

Y ahora el listado en francés debe devolver **`"locale_used": "fr"`** para el Menú A —
esta vez de verdad, porque el idioma existe:

```bash
curl -s "http://localhost:8000/api/menus/public/available?locale=fr" \
  | jq '.items[] | {name, locale_used}'
```

---

### Caso 5 — No se rompió el flujo normal (regresión)

```bash
curl -s "http://localhost:8000/api/menus/public/available?locale=es-ES" | jq '.items | length'
curl -i "http://localhost:8000/api/menus/$MENU_A/render?locale=es-ES"
```

✅ **Pasa si:** el listado devuelve los menús esperados y el render del Menú A responde
`200` con `meta.title = "Menú del día"`.

---

## Resumen de resultados esperados

| Caso | Petición | Esperado |
|---|---|---|
| 1 | `render` del Menú B (roto) | `200` (antes 500) |
| 2 | `available?locale=fr` | Ningún `locale_used` inventado; Menú C omitido |
| 3 | `render` de cada item con su `locale_used` | **Todos `200`** |
| 4.a | `publish/fr` sin contenido | `409` |
| 4.b | `publish/fr` con contenido | `200` |
| 5 | Flujo normal es-ES | `200`, sin cambios |

---

## 6. Limpieza

```bash
docker-compose exec mongo mongosh aralar --quiet --eval '
db.menus.deleteMany({ template_slug: "qa-fix-locale" });
db.menu_templates.deleteMany({ slug: "qa-fix-locale" });
print("limpiado");
'
```

---

## Nota sobre el reporte anterior

El script de pruebas original repetía la misma petición en los pasos 3 y 4 (ambos
`render?locale=es-ES` sobre el mismo id), así que el caso `fr` nunca llegó a probarse.
El **Caso 3** de esta guía lo cubre correctamente al recorrer todos los items del listado.
