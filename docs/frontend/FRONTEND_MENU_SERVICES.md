# Servicios de menú — "Otros servicios"

> Guía de implementación para el frontend. Cubre qué cambió en la API, los
> endpoints nuevos, el CRUD del catálogo, la propuesta de UI y los casos borde.
> Referencia rápida en `FRONTEND_GUIDE.md` §3.5.

---

## 1. Qué problema resuelve

La landing tiene dos zonas distintas que muestran menús:

| Zona | Endpoint | Qué muestra |
|---|---|---|
| **Listas de Menús** | `GET /api/menus/public/available` | Los menús "normales" del día |
| **Otros servicios** | `GET /api/menus/public/services/{slug}` | Menús de un servicio concreto (Desayunos, Lunch, Comida para llevar…) |

Sistemáticamente **es el mismo objeto Menú**. Lo que cambia es dónde se lista, y
eso lo decide un campo nuevo del menú: `service_slugs`.

**Regla central — son dos lugares excluyentes:**

- Menú con `service_slugs` **no vacío** → sale **solo** en su(s) servicio(s).
  **Desaparece de `/public/available`.**
- Menú con `service_slugs` **vacío** (`[]`) → menú normal, sale en
  `/public/available` como siempre.

No hay superposición. Si un menú "desapareció" del listado general, casi siempre
es porque alguien le asignó un servicio.

---

## 2. Qué cambió (resumen para migrar el front)

| Cambio | Impacto en el front |
|---|---|
| Campo nuevo `service_slugs: string[]` en el menú | Aparece en `GET /api/menus/{id}`, en el listado admin y en los items públicos. Default `[]`. |
| `/public/available` ahora **excluye** menús con servicios | Si ya consumes este endpoint, no hay que tocar nada; simplemente dejarán de venir los clasificados. |
| Endpoint nuevo `GET /api/menus/public/services/{slug}` | Nueva vista "Otros servicios". |
| Colección/CRUD nuevo `/api/menu-services` | Nueva pantalla de administración del catálogo de servicios. |
| Endpoint público `GET /api/menu-services/public` | Alimenta los tabs/tarjetas de la sección. |
| Permisos nuevos `menu_services:{read,create,update,delete}` | El panel debe ocultar la gestión si el usuario no los tiene. |

**Nada de lo existente rompe:** los menús ya creados quedan con `service_slugs: []`
tras la migración, así que siguen apareciendo exactamente donde estaban.

---

## 3. Parte pública (landing)

### 3.1 Listar los servicios (tabs de la sección)

```http
GET /api/menu-services/public?locale=es-ES[&tenant_id=aralar]
```

```json
{
  "items": [
    { "slug": "desayunos", "name": "Desayunos", "label": "Desayunos", "order": 1 },
    { "slug": "lunch", "name": "Lunch", "label": "Lunch", "order": 2 },
    { "slug": "comida-para-llevar", "name": "Comida para llevar", "label": "Takeaway", "order": 3 }
  ]
}
```

- Público, sin auth.
- Solo servicios **activos**, ya ordenados por `order` → **respeta el orden del array**.
- Pinta **`label`** (resuelto por `locale`; si no hay label en ese idioma cae al
  primer label disponible y, si no hay ninguno, a `name`).
- Usa **`slug`** para la siguiente llamada. Nunca muestres el slug al usuario.

### 3.2 Listar los menús de un servicio

```http
GET /api/menus/public/services/{slug}?locale=es-ES&tz=Europe/Madrid[&fallback=en-GB][&date=YYYY-MM-DD][&images_limit=10]
```

Devuelve **exactamente el mismo formato de tarjeta** que `/public/available`:

```json
{
  "items": [
    {
      "id": "665f...",
      "name": "Desayuno continental",
      "template_slug": "desayuno-basico",
      "template_version": 2,
      "updated_at": "2026-07-19T10:00:00Z",
      "list_order": 1,
      "service_slugs": ["desayunos"],
      "locale_used": "es-ES",
      "title": "Desayuno continental",
      "summary": "Café, bollería y zumo",
      "preview_images": ["https://cdn/…webp"]
    }
  ]
}
```

- Mismos filtros de disponibilidad que el listado general (día de la semana,
  rango de fechas, timezone).
- **Ya vienen ordenados** por `list_order` (menor primero, `null` al final,
  empate por `updated_at` desc) — el mismo criterio del listado general. No
  reordenes en cliente.
- Al hacer clic: `GET /api/menus/{id}/render?locale={locale_used}` como siempre.
  **Usa `locale_used`, no el locale que pediste**, o puedes comerte un 409.
- Slug inexistente → `{"items": []}` (no es error).

### 3.3 Flujo completo de la sección

```
GET /api/menu-services/public?locale=es-ES   → tabs
        ↓ (usuario elige "desayunos")
GET /api/menus/public/services/desayunos?locale=es-ES&tz=Europe/Madrid  → tarjetas
        ↓ (usuario abre una)
GET /api/menus/{id}/render?locale={locale_used}&include_ui=true  → detalle
```

---

## 4. Parte privada — CRUD del catálogo

Todos requieren JWT. Prefijo `/api/menu-services`.

| Verbo | Ruta | Permiso | Notas |
|---|---|---|---|
| `POST` | `/api/menu-services` | `menu_services:create` | Crea un servicio |
| `GET` | `/api/menu-services` | `menu_services:read` | Lista **incluidos inactivos** |
| `GET` | `/api/menu-services/{id}` | `menu_services:read` | Detalle |
| `PUT` | `/api/menu-services/{id}` | `menu_services:update` | Edita (**slug no**, ver §6) |
| `DELETE` | `/api/menu-services/{id}` | `menu_services:delete` | **409** si hay menús usándolo |

### Crear

```http
POST /api/menu-services
{
  "tenant_id": "aralar",
  "slug": "brunch",
  "name": "Brunch",
  "labels": { "es-ES": "Brunch", "en-GB": "Brunch" },
  "order": 4,
  "is_active": true
}
```

- `slug` se **normaliza**: se recorta, pasa a minúsculas y los espacios se
  vuelven guiones (`"Comida Para Llevar"` → `"comida-para-llevar"`).
- `slug` es **único por tenant** → duplicado devuelve **409**.
- `labels` es el nombre visible por idioma. `name` es el nombre interno del panel.
- `order` controla la posición en la sección pública.

### Listar (admin)

```http
GET /api/menu-services?tenant_id=aralar[&is_active=true]
→ { "items": [ …servicios completos… ], "total": 3 }
```

A diferencia del público, aquí **sí vienen los inactivos** (para poder reactivarlos).

### Editar

```http
PUT /api/menu-services/{id}
{ "name": "Brunch de fin de semana", "labels": {...}, "order": 2, "is_active": true }
```

Campos editables: `name`, `labels`, `order`, `is_active`. **`slug` no** — mandarlo
devuelve **422** (ver §6, es importante).

### Borrar

```http
DELETE /api/menu-services/{id}
→ 200 { "message": "ok" }
→ 409 { "message": "service is referenced by 3 menu(s)" }
```

Si da 409: primero quita ese servicio de los menús (o desactívalo en vez de borrarlo).

---

## 5. Clasificar un menú

Se hace con el endpoint que **ya existía**, no hay uno nuevo:

```http
PUT /api/menus/{id}/general        (permiso menus:update)
{ "service_slugs": ["desayunos", "lunch"] }
```

| Payload | Efecto |
|---|---|
| `{"service_slugs": ["desayunos"]}` | El menú pasa a "Otros servicios" y **sale de** `/public/available` |
| `{"service_slugs": ["desayunos","lunch"]}` | Aparece en ambos servicios |
| `{"service_slugs": []}` | Quita la clasificación → **vuelve a** `/public/available` |
| Campo ausente | No se toca (puedes actualizar solo `name` sin perder la clasificación) |

**Validación:** cada slug debe existir y estar **activo** para el tenant del menú.
Si no → **400** `{"message": "unknown or inactive service: xxx"}`.
Los slugs se normalizan y deduplican (`["  Desayunos ", "desayunos"]` → `["desayunos"]`).

**Al duplicar** un menú (`POST /api/menus/{id}/duplicate`), la copia **hereda**
`service_slugs` (a diferencia de `featured`/`list_order`, que se resetean). La
clasificación se considera identidad del menú, no posición.

---

## 6. ⚠️ El slug de un servicio es INMUTABLE

**Por qué importa:** los menús guardan el slug como **texto** en `service_slugs`,
sin relación por id y **sin cascada**. Si se pudiera renombrar `desayunos` →
`almuerzos`, pasaría esto:

1. El servicio pasa a llamarse `almuerzos`.
2. Los menús siguen guardando `["desayunos"]`.
3. `GET /public/services/almuerzos` → **vacío**.
4. `GET /public/available` → **tampoco los muestra** (están clasificados).

Los menús quedarían **huérfanos: publicados pero inalcanzables desde ambos sitios**,
y en silencio. Por eso el backend **no acepta `slug` en el `PUT`** (responde `422`).

**Qué hacer en la UI:**
- El campo `slug` se pide **solo al crear** y luego se muestra **deshabilitado /
  solo lectura** (o directamente no se muestra).
- Para "renombrar" un servicio de cara al público, se edita **`labels`** (y `name`
  para el panel). Eso es lo que ve el usuario final; el slug es una clave técnica.
- Si de verdad hace falta otro slug: crear servicio nuevo → reasignar los menús →
  borrar el viejo.

### Desactivar (`is_active: false`)

Sí está permitido, pero tiene una consecuencia que hay que avisar: el servicio
desaparece de `/api/menu-services/public` (o sea, de los tabs), **pero sus menús
siguen excluidos de `/public/available`**. En la práctica esos menús quedan
ocultos para el visitante.

Por eso, al desactivar un servicio con menús, la respuesta incluye un extra:

```json
{ "...": "...", "is_active": false, "affected_menus": 3 }
```

**Muestra esa advertencia**: *"3 menús dejarán de ser visibles en la web"*, con
opción de continuar o cancelar. El campo solo aparece cuando se desactiva y hay
menús afectados.

---

## 7. Propuesta de UI

### 7.1 Pantalla nueva: "Servicios" (administración)

Tabla simple con: `label (es-ES)` · `slug` (gris, monoespaciado) · `order` ·
`estado` · acciones.

- **Crear**: modal con `name`, `slug` (autogenerado desde el nombre, editable
  **solo aquí**), `labels` por idioma, `order`, `is_active`.
- **Editar**: mismo modal con el **slug bloqueado** y un tooltip: *"El
  identificador no se puede cambiar porque los menús lo referencian"*.
- **Borrar**: si responde 409, muestra el mensaje del backend y ofrece "Ver menús
  de este servicio" en vez de un error genérico.
- **Toggle activo/inactivo**: si la respuesta trae `affected_menus`, confirma antes.
- Ordenar por `order`; ideal drag & drop que haga `PUT` del `order` de cada uno.

### 7.2 En el editor de Menú: asignar servicios

En el bloque de "datos generales" del menú (donde ya están `name`, `featured` y
`list_order`), añadir un **multi-select de servicios**:

```
Servicios:  [ Desayunos ×]  [ Lunch ×]        ▾
            ℹ️ Un menú con servicios NO aparece en "Listas de Menús".
```

- Opciones = `GET /api/menu-services` filtrando `is_active: true`.
- Se guarda con el mismo `PUT /api/menus/{id}/general` que ya usa esa pantalla:
  simplemente incluye `service_slugs` en el payload.
- **Aviso contextual imprescindible**: al añadir el primer servicio, indicar que
  el menú saldrá del listado general. Es el comportamiento que más va a
  sorprender al editor.
- Al quitar todos, avisar que vuelve al listado general.

> Alternativa más simple si el multi-select es mucho: un desplegable "Ubicación
> del menú" con opciones `Listas de Menús` / `Otros servicios → [servicio]`. Es
> más claro conceptualmente, pero limita a un solo servicio por menú; la API
> soporta varios.

### 7.3 En la landing

- Sección "Otros servicios" con tabs/tarjetas desde `/api/menu-services/public`.
- Al elegir uno, tarjetas desde `/api/menus/public/services/{slug}`, con el mismo
  componente de tarjeta que ya usas en "Listas de Menús" (el payload es idéntico).
- Si un servicio devuelve `items: []` (no hay menús disponibles hoy), decide si
  ocultas el tab o muestras un vacío amable.

---

## 8. Backend / despliegue

Antes de que el frontend pueda usar esto, en cada entorno hay que correr:

```bash
docker-compose exec api python scripts/migrate.py
```

Eso aplica:
- **014** — crea la colección `menu_services` con sus índices, siembra los 3
  servicios iniciales (`desayunos`, `lunch`, `comida-para-llevar`) y normaliza
  los menús existentes a `service_slugs: []`.
- **015** — sincroniza los permisos `menu_services:*` y los asigna a los roles
  (admin todos; manager read/create/update).

> Los 3 servicios se siembran con `tenant_id: "aralar"`. Si el tenant real es
> otro, hay que ajustarlo antes de migrar.

---

## 9. Resumen de errores

| Código | Cuándo | Qué mostrar |
|---|---|---|
| `400` | `service_slugs` con un slug inexistente o inactivo | "El servicio X no existe o está desactivado" |
| `409` | Crear servicio con slug repetido | "Ya existe un servicio con ese identificador" |
| `409` | Borrar servicio con menús asociados | Mensaje del backend + enlace a esos menús |
| `422` | Mandar `slug` en el `PUT` de un servicio | No debería ocurrir: el campo va deshabilitado |
| `403` | Falta permiso `menu_services:*` | Ocultar la sección de administración |
