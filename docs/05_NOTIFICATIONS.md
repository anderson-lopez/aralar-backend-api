# Flujos de Notificaciones

## ¿Qué es una Notificación?

Las **notificaciones** son avisos o mensajes que el restaurante puede mostrar a sus clientes en la app/web. Pueden ser banners, alertas de horario, promociones, avisos de cierre, etc. Soportan multi-idioma, programación temporal y ubicación en la interfaz.

---

## 1. Ciclo de Vida de una Notificación

```mermaid
stateDiagram-v2
    [*] --> Creada: POST /notifications
    Creada --> Activa: is_active = true (por defecto)
    Activa --> Inactiva: POST /notifications/:id/toggle
    Inactiva --> Activa: POST /notifications/:id/toggle
    Activa --> Editada: PUT /notifications/:id
    Editada --> Activa
    Activa --> Eliminada: DELETE /notifications/:id
    Inactiva --> Eliminada: DELETE /notifications/:id
    Eliminada --> [*]

    note right of Activa: Visible en /active si<br/>la programación coincide
```

---

## 2. Flujo Completo: Crear y Mostrar una Notificación

```mermaid
sequenceDiagram
    actor Admin
    participant API as /api/notifications
    actor Cliente as Cliente Público

    Note over Admin: 1. Crear notificación
    Admin->>API: POST / {title, message, type, priority, location, schedule, ...}
    API-->>Admin: 201 {id, ...}

    Note over Admin: 2. (Opcional) Agregar traducción
    Admin->>API: PUT /:id/locales/en-GB {data: {...}, meta: {...}}
    API-->>Admin: 200

    Note over Cliente: 3. Consulta pública
    Cliente->>API: GET /active?locale=es-ES&tz=Europe/Madrid
    API-->>Cliente: Notificaciones activas ahora
```

---

## 3. Operaciones CRUD (Admin/Manager)

```mermaid
flowchart TD
    subgraph "CRUD"
        CREATE["POST /notifications<br/>Crear notificación<br/>Permiso: notifications:create"]
        READ["GET /notifications<br/>Listar todas<br/>Permiso: notifications:read"]
        GET["GET /notifications/:id<br/>Ver detalle<br/>Permiso: notifications:read"]
        UPDATE["PUT /notifications/:id<br/>Editar<br/>Permiso: notifications:update"]
        DELETE["DELETE /notifications/:id<br/>Eliminar<br/>Permiso: notifications:delete"]
    end

    subgraph "Acciones"
        TOGGLE["POST /notifications/:id/toggle<br/>Activar/Desactivar<br/>Permiso: notifications:update"]
        LOCALE["PUT /notifications/:id/locales/:locale<br/>Traducción por idioma<br/>Permiso: notifications:update"]
    end

    subgraph "Consultas"
        LOCATION["GET /notifications/location/:location<br/>Por ubicación<br/>Permiso: notifications:read"]
        STATS["GET /notifications/stats<br/>Estadísticas<br/>Permiso: notifications:read"]
        EXPIRED["GET /notifications/expired<br/>Expiradas<br/>Permiso: notifications:read"]
        UPCOMING["GET /notifications/upcoming<br/>Próximas<br/>Permiso: notifications:read"]
    end

    CREATE --> TOGGLE
    CREATE --> LOCALE
    CREATE --> UPDATE
```

---

## 4. Filtros de Listado

```mermaid
flowchart LR
    LIST["GET /notifications"] --> FILTERS["Filtros opcionales:<br/>• location (banner, popup, etc.)<br/>• is_active (true/false)<br/>• priority_min<br/>• priority_max"]
```

**Casos de prueba QA:**
- Listar sin filtros → todas las notificaciones
- Filtrar por `location=banner` → solo banners
- Filtrar por `is_active=true` → solo activas
- Filtrar por prioridad → rango de prioridades

---

## 5. Endpoint Público: Notificaciones Activas

```mermaid
sequenceDiagram
    actor Cliente
    participant API as GET /notifications/active

    Cliente->>API: ?locale=es-ES&tz=Europe/Madrid
    API->>API: Evaluar programación temporal<br/>contra fecha/hora actual en tz
    API-->>Cliente: Notificaciones activas ahora

    Note over API: Solo devuelve notificaciones con<br/>is_active=true y dentro del schedule
```

**Casos de prueba QA:**
- Notificación activa + dentro del horario → aparece
- Notificación activa + fuera del horario → NO aparece
- Notificación inactiva → NO aparece (independientemente del horario)
- Sin parámetros → usa timezone por defecto del tenant

---

## 6. Consultas Temporales (Admin)

```mermaid
flowchart TD
    subgraph "Estado temporal"
        ACTIVE["GET /notifications/active<br/>Activas ahora (público)"]
        EXPIRED["GET /notifications/expired<br/>Ya expiradas"]
        UPCOMING["GET /notifications/upcoming<br/>Programadas a futuro"]
    end

    EXPIRED --> NOTE1["Notificaciones cuyo<br/>schedule ya terminó"]
    UPCOMING --> NOTE2["Notificaciones cuyo<br/>schedule aún no empieza"]
    ACTIVE --> NOTE3["Notificaciones dentro<br/>del schedule actual"]
```

**Casos de prueba QA:**
- Notificación con `end_date` en el pasado → aparece en `/expired`
- Notificación con `start_date` en el futuro → aparece en `/upcoming`
- Notificación vigente ahora → aparece en `/active`

---

## 7. Traducciones de Notificaciones

```mermaid
sequenceDiagram
    actor Admin
    participant API as /api/notifications

    Admin->>API: PUT /:id/locales/es-ES {data: {title: "Cerrado lunes", message: "..."}, meta: {...}}
    API-->>Admin: 200

    Admin->>API: PUT /:id/locales/en-GB {data: {title: "Closed Monday", message: "..."}, meta: {...}}
    API-->>Admin: 200

    Note over Admin: El cliente recibe el idioma<br/>según su locale en /active
```

---

## 8. Permisos Requeridos

| Acción | Permiso |
|--------|---------|
| Crear notificación | `notifications:create` |
| Listar / ver notificaciones | `notifications:read` |
| Editar / toggle / traducir | `notifications:update` |
| Eliminar notificación | `notifications:delete` |
| Ver activas (público) | Sin autenticación |

---

## 9. Caso Real: Aviso de Cierre por Festivo

```mermaid
sequenceDiagram
    actor Manager
    participant API

    Note over Manager: El restaurante cierra el 25 de diciembre
    Manager->>API: POST /notifications {<br/>  title: "Cerrado por Navidad",<br/>  message: "El restaurante permanecerá cerrado el 25 de diciembre.",<br/>  type: "warning",<br/>  priority: 10,<br/>  location: "banner",<br/>  schedule: {start: "2025-12-20", end: "2025-12-26"}<br/>}
    API-->>Manager: 201 {id: "notif_123"}

    Manager->>API: PUT /notif_123/locales/en-GB {data: {title: "Closed for Christmas", message: "..."}}
    API-->>Manager: 200

    Note over Manager: Del 20 al 26 de diciembre,<br/>los clientes verán el aviso
```
