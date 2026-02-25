# Flujos de Gestión de Templates

## ¿Qué es un Template?

Un **template** define la **estructura** de un menú: qué secciones tiene (cabecera, platos, postres, vinos…), qué campos tiene cada sección (nombre, precio, imagen, alérgenos…), cuáles son traducibles y cuáles no, y cómo debe renderizarse en el frontend (layout, orden, hints de UI).

Un template se crea una vez y se reutiliza para crear múltiples menús con la misma estructura.

---

## 1. Ciclo de Vida de un Template

```mermaid
stateDiagram-v2
    [*] --> draft: POST /menu-templates (crear)
    draft --> draft: PUT /menu-templates/:id (editar)
    draft --> published: POST /menu-templates/:id/publish
    published --> draft: POST /menu-templates/:id/unpublish
    published --> archived: POST /menu-templates/:id/archive
    draft --> archived: POST /menu-templates/:id/archive
    archived --> [*]

    note right of draft: Solo se puede editar en estado draft
    note right of published: Los menús se crean a partir\nde templates publicados
```

**Casos de prueba QA:**
- Crear template → estado `draft`
- Editar template en `draft` → funciona
- Publicar template → estado `published`, se genera nuevo ID de versión publicada
- Intentar editar template `published` → debe fallar o requerir despublicar primero
- Despublicar → vuelve a `draft`
- Archivar → estado `archived`

---

## 2. Flujo Completo: Crear y Publicar un Template

```mermaid
sequenceDiagram
    actor Editor
    participant API as /api/menu-templates
    participant DB as MongoDB

    Note over Editor: Paso 1 — Crear template (draft)
    Editor->>API: POST / {name, slug, tenant_id, version, sections, ui, i18n}
    API->>DB: Verificar que no exista slug+version duplicado
    alt No existe duplicado
        API->>DB: Insertar template con status=draft
        API-->>Editor: 201 {id: "tmpl_001"}
    else Slug+version ya existe
        API-->>Editor: 409 "conflict"
    end

    Note over Editor: Paso 2 — Iterar sobre el diseño
    Editor->>API: PUT /tmpl_001 {sections: [...actualizado]}
    API-->>Editor: 200 {message: "ok"}

    Note over Editor: Paso 3 — Publicar
    Editor->>API: POST /tmpl_001/publish {notes: "v1 lista"}
    API->>DB: Crear copia publicada, generar nuevo ID
    API-->>Editor: 201 {id: "tmpl_pub_001"}

    Note over Editor: El ID publicado es el que<br/>se usa al crear menús
```

---

## 3. Estructura de un Template (conceptual)

```mermaid
graph TD
    T["Template"] --> META["Metadatos<br/>name, slug, version, tenant_id, status"]
    T --> I18N["i18n<br/>default_locale, locales[]"]
    T --> SECTIONS["sections[]"]
    T --> UI["ui (manifest global)<br/>layout, catalogs"]

    SECTIONS --> S1["Sección: header<br/>repeatable: false"]
    SECTIONS --> S2["Sección: items/starters<br/>repeatable: true<br/>minItems, maxItems"]
    SECTIONS --> S3["Sección: footer<br/>repeatable: false"]

    S1 --> F1["fields[]<br/>title (text, translatable)<br/>date (date, no translatable)"]
    S2 --> F2["fields[]<br/>name (text, translatable)<br/>price (price, no translatable)<br/>allergens (array)"]
    S1 --> UI1["ui por sección<br/>role, order, display, hints"]
    S2 --> UI2["ui por sección<br/>role, order, display, hints"]
```

### Tipos de campo comunes

| Tipo | Ejemplo | Traducible |
|------|---------|------------|
| `text` | Nombre del plato, título | Sí (si `translatable: true`) |
| `date` | Fecha del menú | No |
| `price` | Precio del plato | No |
| `image` | Foto del plato | No (URL) |
| `array` | Alérgenos | No |

---

## 4. Slugs y Versionado

```mermaid
flowchart LR
    subgraph "Template: daily-basic"
        V1["v1 (published)"]
        V2["v2 (draft)"]
    end
    subgraph "Template: seasonal-autumn"
        V1B["v1 (published)"]
    end

    V1 -->|"Menú A"| MA["Menú creado con<br/>daily-basic v1"]
    V1 -->|"Menú B"| MB["Menú creado con<br/>daily-basic v1"]
    V1B -->|"Menú C"| MC["Menú creado con<br/>seasonal-autumn v1"]
```

- Cada template tiene un `slug` (identificador humano) y una `version` (numérica).
- Al crear un menú, se referencia `template_slug` + `template_version`.
- Un template publicado NO se puede editar; para cambiar la estructura, se crea una nueva versión o se despublica primero.

**Casos de prueba QA:**
- Crear template con slug `daily-basic` versión 1 → OK
- Crear otro template con slug `daily-basic` versión 1 → 409 conflicto
- Crear template con slug `daily-basic` versión 2 → OK (nueva versión)

---

## 5. Operaciones CRUD

```mermaid
flowchart TD
    subgraph "Lectura"
        LIST["GET /menu-templates<br/>Listar templates<br/>Filtros: status, slug, tenant_id"]
        GET["GET /menu-templates/:id<br/>Detalle de un template"]
    end

    subgraph "Escritura"
        CREATE["POST /menu-templates<br/>Crear template (draft)"]
        UPDATE["PUT /menu-templates/:id<br/>Editar template (solo draft)"]
    end

    subgraph "Ciclo de vida"
        PUBLISH["POST /menu-templates/:id/publish<br/>Publicar (genera nueva versión)"]
        UNPUBLISH["POST /menu-templates/:id/unpublish<br/>Despublicar (vuelve a draft)"]
        ARCHIVE["POST /menu-templates/:id/archive<br/>Archivar (desactivar)"]
    end

    CREATE --> UPDATE
    UPDATE --> PUBLISH
    PUBLISH --> UNPUBLISH
    PUBLISH --> ARCHIVE
```

---

## 6. Templates Reales del Sistema (ejemplos)

| Slug | Descripción | Secciones principales |
|------|-------------|-----------------------|
| `daily-basic` | Menú del día sencillo | header, items, footer |
| `daily-basic-ui` | Menú del día con UI completo | header, starters, mains, extras, footer |
| `simple-photo` | Menú con fotos | header (banner), dishes (con imágenes) |
| `seasonal-autumn` | Carta estacional | header, starters, mains, desserts, wines, footer |
| `three-sections-multiimages` | Carta 3 secciones con múltiples imágenes | starters, mains_fish, mains_meat, desserts |
| `aralar-allergen-menu` | Menú con alérgenos detallados | header, starters, mains, desserts, extras, footer |

---

## 7. Permisos Requeridos

| Acción | Permiso |
|--------|---------|
| Crear template | `menu_templates:create` |
| Listar / ver templates | `menu_templates:read` |
| Editar template (draft) | `menu_templates:update` |
| Publicar / despublicar | `menu_templates:publish` |
| Archivar | `menu_templates:archive` |

**Caso de prueba QA:**
- Usuario con rol `manager` (sin `menu_templates:create`) intenta crear template → 403
- Admin con todos los permisos puede hacer todas las operaciones
- Manager con permiso extra `menu_templates:create` → puede crear templates
