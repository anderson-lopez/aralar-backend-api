# Sistema de Notificaciones Dinámicas - Guía de Uso

## Descripción

El sistema de notificaciones permite crear mensajes informativos que aparecen automáticamente en la landing page del restaurante según reglas de programación predefinidas.

## Características Principales

- ✅ **Validación de horarios**: Si las fechas son del mismo día, la hora final debe ser posterior a la inicial
- ✅ **Campos en snake_case**: Todos los campos siguen la convención snake_case
- ✅ **Validaciones con abort**: Uso de `abort()` para manejo de errores
- ✅ **Endpoints completos**: CRUD completo + endpoints especializados

## Endpoints Disponibles

### 1. Crear Notificación
```http
POST /api/notifications/
Content-Type: application/json

{
  "name": "Promoción Fin de Semana",
  "content": "🍷 <strong>Oferta especial:</strong> 20% descuento en vinos",
  "is_active": true,
  "priority": 8,
  "scheduling": {
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-12-31T23:59:59Z",
    "days_of_week": ["FRI", "SAT", "SUN"],
    "time_start": "18:00",
    "time_end": "23:30"
  },
  "display": {
    "location": "menu-section",
    "type": "banner",
    "style": {
      "background_color": "#8B0000",
      "text_color": "#FFFFFF",
      "custom_css_class": "wine-promo"
    }
  }
}
```

### 2. Obtener Notificaciones Activas (Público)
```http
GET /api/notifications/active
```

### 3. Listar Todas las Notificaciones
```http
GET /api/notifications/
GET /api/notifications/?location=hero-section
GET /api/notifications/?is_active=true
GET /api/notifications/?priority_min=5&priority_max=10
```

### 4. Obtener Notificación por ID
```http
GET /api/notifications/{id}
```

### 5. Actualizar Notificación
```http
PUT /api/notifications/{id}
Content-Type: application/json

{
  "is_active": false,
  "priority": 5
}
```

### 6. Eliminar Notificación
```http
DELETE /api/notifications/{id}
```

### 7. Toggle Estado de Notificación
```http
POST /api/notifications/{id}/toggle
```

### 8. Obtener por Ubicación
```http
GET /api/notifications/location/hero-section
```

### 9. Estadísticas
```http
GET /api/notifications/stats
```

### 10. Notificaciones Expiradas
```http
GET /api/notifications/expired
```

### 11. Notificaciones Futuras
```http
GET /api/notifications/upcoming
```

## Validaciones Implementadas

### 1. Validación de Horarios
- Si `start_date` y `end_date` son el mismo día:
  - `time_end` debe ser posterior a `time_start`
- Si son días diferentes:
  - `time_end` puede ser anterior a `time_start`

### 2. Validación de Campos
- **name**: 1-100 caracteres, único
- **content**: 1-2000 caracteres
- **priority**: 1-100
- **start_date**: Debe ser anterior a `end_date`
- **time_start/time_end**: Formato HH:MM
- **days_of_week**: Valores válidos: SUN, MON, TUE, WED, THU, FRI, SAT
- **location**: Valores válidos: top-bar, hero-section, menu-section, contact-section, footer, global-modal, global-toast
- **type**: Valores válidos: banner, card, modal, toast
- **background_color/text_color**: Formato hexadecimal (#RRGGBB)

## Ejemplos de Uso

### Ejemplo 1: Promoción de Fin de Semana
```json
{
  "name": "Promoción Weekend",
  "content": "🍷 <strong>Oferta especial de fin de semana:</strong> 20% de descuento en vinos seleccionados",
  "is_active": true,
  "priority": 8,
  "scheduling": {
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-12-31T23:59:59Z",
    "days_of_week": ["FRI", "SAT", "SUN"],
    "time_start": "18:00",
    "time_end": "23:30"
  },
  "display": {
    "location": "menu-section",
    "type": "banner",
    "style": {
      "background_color": "#8B0000",
      "text_color": "#FFFFFF"
    }
  }
}
```

### Ejemplo 2: Aviso de Mantenimiento (Mismo Día)
```json
{
  "name": "Mantenimiento Cocina",
  "content": "⚠️ Servicio limitado mañana por mantenimiento de cocina. Solo disponible menú frío.",
  "is_active": true,
  "priority": 10,
  "scheduling": {
    "start_date": "2025-01-25T08:00:00Z",
    "end_date": "2025-01-25T23:59:59Z",
    "time_start": "08:00",
    "time_end": "18:00"
  },
  "display": {
    "location": "top-bar",
    "type": "banner",
    "style": {
      "background_color": "#FFA500",
      "text_color": "#000000"
    }
  }
}
```

### Ejemplo 3: Modal de Bienvenida
```json
{
  "name": "Bienvenida Nuevos Clientes",
  "content": "<h3>¡Bienvenido a Aralar!</h3><p>Descubre nuestra cocina tradicional con un toque moderno. <strong>Primera consumición gratis</strong> para nuevos clientes.</p>",
  "is_active": true,
  "priority": 5,
  "scheduling": {
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-12-31T23:59:59Z",
    "time_start": "12:00",
    "time_end": "15:00"
  },
  "display": {
    "location": "global-modal",
    "type": "modal",
    "style": {
      "custom_css_class": "welcome-modal"
    }
  }
}
```

## Respuestas de Error

### 400 - Bad Request
```json
{
  "message": "Validation error: {'scheduling': {'time_end': ['Time end must be after time start when scheduling is on the same day']}}"
}
```

### 404 - Not Found
```json
{
  "message": "Notification not found"
}
```

### 500 - Internal Server Error
```json
{
  "message": "Error creating notification: [detalle del error]"
}
```

## Integración con Frontend

El endpoint `/api/notifications/active` está diseñado para ser consumido por el frontend:

```javascript
// Ejemplo de consumo desde JavaScript
async function loadActiveNotifications() {
  try {
    const response = await fetch('/api/notifications/active');
    const notifications = await response.json();
    
    // Renderizar notificaciones en el DOM
    notifications.forEach(notification => {
      renderNotification(notification);
    });
  } catch (error) {
    console.error('Error loading notifications:', error);
  }
}
```

## Migración

Para crear la colección de notificaciones en MongoDB:

```bash
python scripts/migrate.py
```

Esto ejecutará la migración `007_create_notifications_collection.py` que:
- Crea la colección `notifications`
- Establece índices optimizados
- Inserta datos de ejemplo
