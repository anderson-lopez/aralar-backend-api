# Flujos Públicos y Renderizado de Menús

## Contexto

Los endpoints públicos son los que consume la **app o web del cliente final** (el comensal). No requieren autenticación JWT. El sistema evalúa automáticamente qué menús mostrar según la fecha, hora, zona horaria y disponibilidad configurada.

---

## 1. Diagrama General de Endpoints Públicos

```mermaid
flowchart TD
    CLIENT["Cliente / Frontend Público"]

    CLIENT --> AVAIL["GET /menus/public/available<br/>¿Qué menús hay hoy?"]
    CLIENT --> FEAT["GET /menus/public/featured<br/>Menús destacados (landing)"]
    CLIENT --> RENDER["GET /menus/:id/render<br/>Menú completo fusionado"]
    CLIENT --> MULTI["POST /menus/render/multiple<br/>Varios menús de una vez"]
    CLIENT --> NOTIF["GET /notifications/active<br/>Avisos activos"]
    CLIENT --> ALLERG["GET /catalogs/allergens<br/>Lista de alérgenos"]
```

---

## 2. Menús Disponibles Hoy

```mermaid
sequenceDiagram
    actor Cliente
    participant API as GET /menus/public/available
    participant DB as MongoDB

    Cliente->>API: ?locale=es-ES&tz=Europe/Madrid
    API->>DB: Buscar menús con status=published<br/>+ al menos un locale publicado<br/>+ availability que coincida con hoy
    DB-->>API: Menús que cumplen criterios
    API->>API: Resolver meta (title, summary) del locale solicitado
    API-->>Cliente: {items: [{id, name, template_slug, title, summary, updated_at}]}
```

### Parámetros

| Param | Requerido | Descripción |
|-------|-----------|-------------|
| `locale` | Sí | Idioma preferido (e.g., `es-ES`) |
| `tz` | No (default: `Europe/Madrid`) | Zona horaria para evaluar disponibilidad |
| `fallback` | No | Idioma fallback si no existe el locale solicitado |
| `date` | No | Fecha específica para simular (e.g., `2025-09-05`) |

### Lógica de disponibilidad

```mermaid
flowchart TD
    START["Solicitud pública"] --> STATUS{"¿status = published?"}
    STATUS -->|No| EXCL["Excluir"]
    STATUS -->|Sí| LOCALE{"¿Al menos un locale<br/>está publicado?"}
    LOCALE -->|No| EXCL
    LOCALE -->|Sí| DAY{"¿El día actual (en tz)<br/>está en days_of_week?"}
    DAY -->|No| EXCL
    DAY -->|Sí| RANGE{"¿La fecha actual<br/>está dentro de date_ranges?"}
    RANGE -->|No| EXCL
    RANGE -->|Sí| INCL["✅ Incluir en respuesta"]
```

**Casos de prueba QA:**
- Consultar sin parámetro `date` → evalúa la fecha/hora actual
- Consultar con `date=2025-09-05` (viernes) → muestra menús disponibles ese viernes
- Menú publicado sin availability → NO aparece
- Menú con availability pero no publicado → NO aparece
- Menú publicado + disponible hoy → aparece con `title` y `summary` del locale
- Consultar con `locale=fr-FR&fallback=en-GB` → si no hay `fr-FR`, usa `en-GB` para title/summary

---

## 3. Menús Destacados (Featured)

```mermaid
sequenceDiagram
    actor Cliente
    participant API as GET /menus/public/featured
    participant DB as MongoDB

    Cliente->>API: ?locale=es-ES&tz=Europe/Madrid&include_ui=true
    API->>DB: Buscar menús featured=true + published<br/>+ disponibles hoy
    DB-->>API: Menús destacados
    API->>API: Renderizar cada menú (fusionar common + locale)
    API->>API: Ordenar por featured_order ASC
    API-->>Cliente: {items: [{id, name, title, summary, featured_order, data, meta, ui?}]}
```

### Diferencia con `/public/available`

| Aspecto | `/public/available` | `/public/featured` |
|---------|--------------------|--------------------|
| **Filtro** | Todos los publicados + disponibles | Solo los marcados como `featured` |
| **Datos** | Resumen (id, title, summary) | Menú renderizado completo (data + meta) |
| **Uso** | Listado general de menús | Landing page / carrusel de destacados |
| **UI** | No incluye | Puede incluir (`include_ui=true`) |

**Casos de prueba QA:**
- Menú featured + publicado + disponible → aparece en featured
- Menú featured pero no publicado → NO aparece
- Ordenamiento: `featured_order=1` aparece antes que `featured_order=5`
- Con `include_ui=true` → respuesta incluye manifest de UI del template

---

## 4. Renderizar un Menú Específico

```mermaid
sequenceDiagram
    actor Cliente
    participant API as GET /menus/:id/render
    participant DB as MongoDB

    Cliente->>API: ?locale=es-ES&fallback=en-GB&with_ui=1
    API->>DB: Obtener menú por ID
    API->>DB: Obtener template asociado

    API->>API: 1. Tomar datos de common (precios, fechas, imágenes)
    API->>API: 2. Fusionar con locale es-ES (nombres, títulos)
    API->>API: 3. Si falta es-ES, usar fallback en-GB
    API->>API: 4. Resolver meta (title, summary)
    API->>API: 5. Si with_ui=1, incluir UI manifest del template

    API-->>Cliente: JSON fusionado completo
```

### Proceso de Fusión (Merge)

```mermaid
flowchart LR
    COMMON["common<br/>{header: {date: '2025-09-05'},<br/>items: [{_id: 'gazpacho', price: 5.5}]}"]
    LOCALE["locales.es-ES.data<br/>{header: {title: 'Menú del día'},<br/>items: [{_id: 'gazpacho', name: 'Gazpacho'}]}"]

    COMMON --> MERGE["Fusión"]
    LOCALE --> MERGE

    MERGE --> RESULT["Resultado renderizado<br/>{header: {title: 'Menú del día', date: '2025-09-05'},<br/>items: [{_id: 'gazpacho', name: 'Gazpacho', price: 5.5}]}"]
```

### Estructura de la Respuesta

```mermaid
graph TD
    RESP["Respuesta de /render"] --> ID["id"]
    RESP --> NAME["name"]
    RESP --> TENANT["tenant_id"]
    RESP --> TMPL["template: {slug, version}"]
    RESP --> LOC["locale (idioma usado)"]
    RESP --> FB["fallback_used (null o idioma alternativo)"]
    RESP --> PUB["published_at"]
    RESP --> UPD["updated_at"]
    RESP --> M["meta: {title, summary}"]
    RESP --> DATA["data: {secciones fusionadas}"]
    RESP --> UI["ui (opcional, si with_ui=1)<br/>{layout, sections[], catalogs}"]
```

### Fallback de Idioma

```mermaid
flowchart TD
    REQ["locale=fr-FR, fallback=en-GB"] --> CHECK{"¿Existe locale fr-FR<br/>publicado?"}
    CHECK -->|Sí| USE_FR["Usar datos de fr-FR<br/>fallback_used = null"]
    CHECK -->|No| FB{"¿Existe fallback en-GB<br/>publicado?"}
    FB -->|Sí| USE_EN["Usar datos de en-GB<br/>fallback_used = 'en-GB'"]
    FB -->|No| EMPTY["Datos vacíos o parciales"]
```

**Casos de prueba QA:**
- Render con `locale=es-ES` → datos en español, `fallback_used=null`
- Render con `locale=fr-FR&fallback=en-GB` → si no hay FR, usa EN, `fallback_used="en-GB"`
- Render con `with_ui=1` → incluye secciones UI con roles, order, display, hints
- Render sin `with_ui` → no incluye manifest UI
- Render con ID inválido → 400
- Render sin locale → 400

---

## 5. Renderizar Múltiples Menús

```mermaid
sequenceDiagram
    actor Cliente
    participant API as POST /menus/render/multiple

    Cliente->>API: {menu_ids: ["id1","id2","id3"], locale: "es-ES", include_ui: true}
    API->>API: Renderizar cada menú individualmente
    API-->>Cliente: {items: [{menú1 renderizado}, {menú2 renderizado}, ...]}

    Note over API: Máximo 10 menús por request
```

**Casos de prueba QA:**
- Enviar 3 IDs válidos → recibe 3 menús renderizados
- Enviar más de 10 IDs → validación de límite
- Enviar ID inválido → 400

---

## 6. Flujo Completo del Cliente

```mermaid
flowchart TD
    START["Cliente abre la app/web"] --> LANDING{"¿Landing page?"}

    LANDING -->|Sí| FEAT["GET /menus/public/featured<br/>?locale=es-ES&tz=Europe/Madrid&include_ui=true"]
    FEAT --> SHOW_FEAT["Mostrar carrusel de menús destacados"]

    LANDING -->|No| LIST["GET /menus/public/available<br/>?locale=es-ES&tz=Europe/Madrid"]
    LIST --> SHOW_LIST["Mostrar lista de menús disponibles hoy"]

    SHOW_FEAT --> SELECT["Cliente selecciona un menú"]
    SHOW_LIST --> SELECT

    SELECT --> RENDER["GET /menus/:id/render<br/>?locale=es-ES&with_ui=1"]
    RENDER --> DISPLAY["Mostrar menú completo con:<br/>• Título y subtítulo<br/>• Platos con nombres y precios<br/>• Imágenes<br/>• Alérgenos<br/>• Notas de pie"]

    DISPLAY --> ALLERG["GET /catalogs/allergens?locale=es-ES"]
    ALLERG --> ICONS["Mostrar iconos de alérgenos"]
```

---

## 7. Catálogo de Alérgenos (Público)

```mermaid
sequenceDiagram
    actor Cliente
    participant API as GET /catalogs/allergens

    Cliente->>API: ?locale=es-ES
    API-->>Cliente: {items: [{code: "gluten", icon: "agluten", label: "Gluten"}, ...]}
```

Los 14 alérgenos europeos están disponibles:

| Código | Icono | ES | EN |
|--------|-------|----|----|
| gluten | agluten | Gluten | Gluten |
| crustaceans | acrusta | Crustáceos | Crustaceans |
| eggs | aegg | Huevos | Eggs |
| fish | afish | Pescado | Fish |
| peanuts | apeanut | Cacahuetes | Peanuts |
| soy | asoy | Soja | Soy |
| milk | amilk | Leche/Lactosa | Milk |
| nuts | anuts | Frutos secos | Tree nuts |
| celery | acelery | Apio | Celery |
| mustard | amustard | Mostaza | Mustard |
| sesame | asesame | Sésamo | Sesame |
| sulfites | asulfite | Sulfitos | Sulphites |
| lupin | alupin | Altramuces | Lupin |
| molluscs | amollusc | Moluscos | Molluscs |

**Casos de prueba QA:**
- Sin locale → devuelve todos los campos (labels multi-idioma)
- Con `locale=es-ES` → incluye campo `label` en español
- Con `locale=en-GB` → incluye campo `label` en inglés
