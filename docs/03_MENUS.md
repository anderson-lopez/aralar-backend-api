# Flujos de Gestión de Menús

## ¿Qué es un Menú?

Un **menú** es una instancia concreta creada a partir de un template publicado. Contiene los datos reales del restaurante para un día o periodo: platos, precios, imágenes, traducciones y configuración de disponibilidad.

---

## 1. Ciclo de Vida de un Menú

```mermaid
stateDiagram-v2
    [*] --> draft: POST /menus (crear)

    draft --> draft: PUT /menus/:id/common
    draft --> draft: PUT /menus/:id/general
    draft --> draft: PUT /menus/:id/locales/:locale
    draft --> draft: PUT /menus/:id/availability
    draft --> draft: POST /menus/:id/publish/:locale

    draft --> published: POST /menus/:id/publish
    published --> draft: POST /menus/:id/unpublish
    published --> archived: POST /menus/:id/archive
    draft --> archived: POST /menus/:id/archive
    archived --> [*]

    note right of draft: Se puede editar libremente
    note right of published: Visible para el público<br/>si la disponibilidad coincide
    note left of archived: Menú desactivado
```

---

## 2. Flujo Completo: Crear un Menú (paso a paso)

```mermaid
sequenceDiagram
    actor Editor
    participant API as /api/menus
    participant DB as MongoDB

    Note over Editor: 1. Crear menú (draft)
    Editor->>API: POST / {tenant_id, name, template_slug, template_version, common}
    API->>DB: Buscar template publicado por slug+version
    alt Template encontrado
        API->>DB: Insertar menú con status=draft
        API-->>Editor: 201 {_id, name, template_slug, ...}
    else Template no encontrado
        API-->>Editor: 400 "template not found"
    end

    Note over Editor: 2. Configurar disponibilidad
    Editor->>API: PUT /:id/availability {timezone, days_of_week, date_ranges}
    API-->>Editor: 200 {message: "ok"}

    Note over Editor: 3. Agregar traducción ES
    Editor->>API: PUT /:id/locales/es-ES {data: {...}, meta: {title, summary}}
    API-->>Editor: 200 {message: "ok"}

    Note over Editor: 4. (Opcional) Agregar traducción EN
    Editor->>API: PUT /:id/locales/en-GB {data: {...}, meta: {title, summary}}
    API-->>Editor: 200 {message: "ok"}

    Note over Editor: 5. Publicar locale(s)
    Editor->>API: POST /:id/publish/es-ES
    API-->>Editor: 200 {message: "ok"}

    Note over Editor: 6. Validar antes de publicar globalmente
    Editor->>API: GET /:id/validate
    alt Todo correcto
        API-->>Editor: 200 {message: "ok"}
    else Faltan requisitos
        API-->>Editor: 200 {message: "invalid", issues: [...]}
    end

    Note over Editor: 7. Publicar globalmente
    Editor->>API: POST /:id/publish
    alt Validación OK
        API-->>Editor: 200 {message: "ok"}
    else Faltan requisitos
        API-->>Editor: 409 "issues..."
    end
```

---

## 3. Requisitos para Publicar un Menú

```mermaid
flowchart TD
    PUBLISH["POST /menus/:id/publish"] --> CHECK{Validar requisitos}

    CHECK --> R1{"¿Tiene availability<br/>configurada?"}
    CHECK --> R2{"¿Al menos un locale<br/>está publicado?"}

    R1 -->|No| FAIL["409 — Issues:<br/>availability is required"]
    R2 -->|No| FAIL2["409 — Issues:<br/>at least one locale must be published"]

    R1 -->|Sí| OK
    R2 -->|Sí| OK["200 — Publicado<br/>status = published"]
```

**Casos de prueba QA:**
- Crear menú → publicar sin availability → 409
- Crear menú → agregar availability → publicar sin locales → 409
- Crear menú → availability + locale publicado → publicar → 200

---

## 4. Estructura de Datos del Menú

```mermaid
graph TD
    MENU["Menú"] --> GENERAL["Datos generales<br/>name, tenant_id, status<br/>featured, featured_order"]
    MENU --> TMPL["Referencia al template<br/>template_id, template_slug<br/>template_version"]
    MENU --> COMMON["common (no traducible)<br/>Precios, fechas, alérgenos<br/>imágenes, IDs de platos"]
    MENU --> LOCALES["locales (traducible)<br/>es-ES: {data, meta}<br/>en-GB: {data, meta}"]
    MENU --> PUBLISH["publish (estado por locale)<br/>es-ES: {status, published_at}<br/>en-GB: {status, published_at}"]
    MENU --> AVAIL["availability<br/>timezone, days_of_week<br/>date_ranges"]
    MENU --> META_TS["Timestamps<br/>created_at, updated_at"]
```

### Separación common vs locales

| Tipo | Dónde va | Ejemplos |
|------|----------|----------|
| **No traducible** | `common` | Precios, fechas, alérgenos, URLs de imágenes, IDs de platos |
| **Traducible** | `locales.{locale}.data` | Nombres de platos, títulos, descripciones |
| **Meta (SEO/UI)** | `locales.{locale}.meta` | `title` y `summary` para listados públicos |

---

## 5. Edición de Datos Comunes (common)

```mermaid
sequenceDiagram
    actor Editor
    participant API as PUT /menus/:id/common

    Editor->>API: {common: {header: {date: "2025-09-06"}, items: [{_id: "plato1", price: 6.5}]}}
    API-->>Editor: 200 {message: "ok"}

    Note over Editor: Cambia precios, fechas, alérgenos<br/>sin afectar traducciones
```

---

## 6. Edición de Propiedades Generales

```mermaid
sequenceDiagram
    actor Editor
    participant API as PUT /menus/:id/general

    Editor->>API: {name: "Nuevo nombre", featured: true, featured_order: 1}
    API-->>Editor: 200 (menú actualizado)

    Note over Editor: Permite editar: name, featured, featured_order
```

---

## 7. Flujo de Traducciones (Locales)

```mermaid
flowchart LR
    subgraph "Paso 1: Rellenar locale"
        PUT_ES["PUT /menus/:id/locales/es-ES<br/>{data: {header: {title: 'Menú del día'}, items: [...]}, meta: {title, summary}}"]
        PUT_EN["PUT /menus/:id/locales/en-GB<br/>{data: {header: {title: 'Daily Menu'}, items: [...]}, meta: {title, summary}}"]
    end

    subgraph "Paso 2: Publicar locale"
        PUB_ES["POST /menus/:id/publish/es-ES"]
        PUB_EN["POST /menus/:id/publish/en-GB"]
    end

    PUT_ES --> PUB_ES
    PUT_EN --> PUB_EN
```

**Casos de prueba QA:**
- Agregar locale `es-ES` → datos guardados correctamente
- Agregar locale `en-GB` → datos guardados sin afectar `es-ES`
- Publicar `es-ES` → el menú se puede consultar en español
- Consultar con `locale=fr-FR&fallback=en-GB` → si no hay `fr-FR`, se usa `en-GB`

---

## 8. Configuración de Disponibilidad

```mermaid
flowchart TD
    AVAIL["PUT /menus/:id/availability"] --> BODY["{<br/>timezone: 'Europe/Madrid',<br/>days_of_week: ['THU','FRI'],<br/>date_ranges: [{start: '2025-09-01', end: '2025-12-31'}]<br/>}"]

    BODY --> EVAL["El sistema evalúa automáticamente<br/>si el menú debe mostrarse"]

    EVAL --> HOY{"¿Hoy es jueves o viernes<br/>en Europe/Madrid?"}
    HOY -->|Sí| RANGO{"¿Hoy está dentro de<br/>2025-09-01 a 2025-12-31?"}
    RANGO -->|Sí| VISIBLE["✅ Menú aparece en<br/>/public/available"]
    HOY -->|No| HIDDEN["❌ Menú NO aparece"]
    RANGO -->|No| HIDDEN
```

**Casos de prueba QA:**
- Menú disponible solo jueves y viernes → consultar un miércoles → no aparece
- Menú con rango septiembre-diciembre → consultar en enero → no aparece
- Usar `?date=2025-09-05` (viernes) → aparece independientemente del día real

---

## 9. Menú Destacado (Featured)

```mermaid
sequenceDiagram
    actor Editor
    participant API

    Editor->>API: PUT /menus/:id/featured {featured: true, featured_order: 1}
    API-->>Editor: 200 {message: "ok"}

    Note over Editor: El menú ahora aparece en<br/>GET /public/featured<br/>ordenado por featured_order
```

Alternativa usando el endpoint general:
```
PUT /menus/:id/general {featured: true, featured_order: 1}
```

**Casos de prueba QA:**
- Marcar menú como featured → aparece en `/public/featured`
- Desmarcar featured → desaparece de `/public/featured`
- `featured_order` más bajo = mayor prioridad (1 aparece antes que 5)
- Al desmarcar `featured`, `featured_order` se limpia automáticamente a `null`

---

## 10. Archivar / Despublicar

```mermaid
flowchart TD
    PUB["Menú publicado"] --> UNPUB["POST /menus/:id/unpublish<br/>→ status vuelve a 'draft'<br/>→ desaparece del público"]
    PUB --> ARCH["POST /menus/:id/archive<br/>→ status = 'archived'<br/>→ menú desactivado"]
    DRAFT["Menú draft"] --> ARCH
```

**Casos de prueba QA:**
- Menú publicado → despublicar → ya no aparece en `/public/available`
- Menú publicado → archivar → ya no aparece en ningún listado público
- Archivar menú ya archivado → responde "already archived"

---

## 11. Listado y Búsqueda de Menús (Admin)

```mermaid
flowchart LR
    LIST["GET /menus"] --> FILTERS["Filtros disponibles:<br/>• status (draft/published/archived)<br/>• tenant_id<br/>• name (búsqueda parcial)<br/>• template_slug<br/>• template_version<br/>• skip, limit (paginación)"]
    DETAIL["GET /menus/:id"] --> FULL["Documento completo<br/>con common, locales, publish, availability"]
```

**Casos de prueba QA:**
- Listar sin filtros → todos los menús
- Filtrar por `status=published` → solo publicados
- Filtrar por `name=diario` → búsqueda parcial case-insensitive
- Filtrar por `template_slug=daily-basic` → solo menús de ese template
- Paginación: `skip=0&limit=5` → primeros 5 resultados

---

## 12. Permisos Requeridos

| Acción | Permiso |
|--------|---------|
| Crear menú | `menus:create` |
| Listar / ver menús | `menus:read` |
| Editar common, locales, availability, general, featured | `menus:update` |
| Publicar / despublicar menú y locales | `menus:publish` |
| Archivar menú | `menus:archive` |
| Validar menú | `menus:read` |
