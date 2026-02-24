# Simulación Menú Diario Básico con UI y Meta

Este documento simula la creación completa de un menú diario básico utilizando las nuevas funcionalidades de UI manifest y metadatos (meta) para títulos y resúmenes.

## Objetivo del Menú

- **Menú diario simple**: Entrante + Principal + Extras + Precio
- **UI Manifest**: Información completa de layout y secciones
- **Metadatos**: Título y resumen para listados públicos
- **Multiidioma**: Soporte para español e inglés
- **Precio fijo**: 12,90 € con IVA incluido

---

## 1. Crear TEMPLATE (draft) con UI por sección

```http
POST /api/menu-templates
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "name": "Menú diario básico (UI)",
  "slug": "daily-basic-ui",
  "tenant_id": "aralar",
  "version": 1,
  "status": "draft",
  "i18n": {
    "default_locale": "es-ES",
    "locales": ["es-ES", "en-GB"]
  },
  "sections": [
    {
      "key": "header",
      "label": {
        "es-ES": "Cabecera",
        "en-GB": "Header"
      },
      "repeatable": false,
      "fields": [
        {
          "key": "title",
          "type": "text",
          "required": true,
          "translatable": true
        },
        {
          "key": "subtitle",
          "type": "text",
          "required": false,
          "translatable": true
        }
      ],
      "ui": {
        "role": "header",
        "order": 0,
        "display": "hero"
      }
    },
    {
      "key": "starters",
      "label": {
        "es-ES": "Entrantes",
        "en-GB": "Starters"
      },
      "repeatable": true,
      "fields": [
        {
          "key": "_id",
          "type": "text",
          "required": true,
          "translatable": false
        },
        {
          "key": "name",
          "type": "text",
          "required": true,
          "translatable": true
        }
      ],
      "ui": {
        "role": "course_list",
        "order": 10,
        "display": "list",
        "hints": {
          "choose_count": 1,
          "scope": "per_person",
          "show_price": false
        }
      }
    },
    {
      "key": "mains",
      "label": {
        "es-ES": "Platos principales",
        "en-GB": "Mains"
      },
      "repeatable": true,
      "fields": [
        {
          "key": "_id",
          "type": "text",
          "required": true,
          "translatable": false
        },
        {
          "key": "name",
          "type": "text",
          "required": true,
          "translatable": true
        }
      ],
      "ui": {
        "role": "course_list",
        "order": 20,
        "display": "list",
        "hints": {
          "choose_count": 1,
          "scope": "per_person",
          "show_price": false
        }
      }
    },
    {
      "key": "extras",
      "label": {
        "es-ES": "Incluye",
        "en-GB": "Includes"
      },
      "repeatable": true,
      "fields": [
        {
          "key": "_id",
          "type": "text",
          "required": true,
          "translatable": false
        },
        {
          "key": "text",
          "type": "text",
          "required": true,
          "translatable": true
        }
      ],
      "ui": {
        "role": "extras",
        "order": 30,
        "display": "bullets"
      }
    },
    {
      "key": "footer",
      "label": {
        "es-ES": "Precio",
        "en-GB": "Price"
      },
      "repeatable": false,
      "fields": [
        {
          "key": "price_total",
          "type": "price",
          "currency": "EUR",
          "required": true,
          "translatable": false
        },
        {
          "key": "vat_percent",
          "type": "number",
          "required": true,
          "translatable": false
        },
        {
          "key": "vat_included",
          "type": "boolean",
          "required": true,
          "translatable": false
        }
      ],
      "ui": {
        "role": "price_footer",
        "order": 40,
        "display": "footer_price"
      }
    }
  ],
  "ui": {
    "layout": "sections",
    "catalogs": {
      "currency": {
        "code": "EUR",
        "symbol": "€",
        "locale": "es-ES"
      }
    }
  }
}
```

**Respuesta esperada:**

```json
{
  "id": "6730a1000000000000000001"
}
```

---

## 2. Publicar TEMPLATE (v1)

```http
POST /api/menu-templates/6730a1000000000000000001/publish
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "notes": "v1 inicial - Menú diario básico con UI"
}
```

**Respuesta esperada:**

```json
{
  "id": "6730a1000000000000000002"
}
```

---

## 3. Crear MENÚ (draft)

Solo datos comunes no traducibles + estructura de items:

```http
POST /api/menus
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "tenant_id": "aralar",
  "name": "Menú diario básico UI",
  "template_slug": "daily-basic-ui",
  "template_version": 1,
  "status": "draft",
  "common": {
    "footer": {
      "price_total": 12.9,
      "vat_percent": 10,
      "vat_included": true
    },
    "extras": [
      {
        "_id": "bread-water"
      }
    ],
    "starters": [{ "_id": "soup" }, { "_id": "salad" }],
    "mains": [{ "_id": "chicken" }, { "_id": "pasta" }]
  }
}
```

**Respuesta esperada:**

```json
{
  "_id": "6730a1000000000000000003",
  "name": "Menú diario básico UI",
  "template_slug": "daily-basic-ui",
  "template_version": 1,
  "status": "draft",
  "common": {
    "footer": { "price_total": 12.9, "vat_percent": 10, "vat_included": true },
    "extras": [{ "_id": "bread-water" }],
    "starters": [{ "_id": "soup" }, { "_id": "salad" }],
    "mains": [{ "_id": "chicken" }, { "_id": "pasta" }]
  },
  "locales": {},
  "publish": {}
}
```

---

## 4. Configurar Disponibilidad (JUE/VIE)

```http
PUT /api/menus/6730a1000000000000000003/availability
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "timezone": "Europe/Madrid",
  "days_of_week": ["THU", "FRI"],
  "date_ranges": [
    {
      "start": "2025-09-01",
      "end": "2025-12-31"
    }
  ]
}
```

**Respuesta esperada:**

```json
{
  "message": "ok"
}
```

---

## 5. Localización es-ES (contenido y meta traducible)

```http
PUT /api/menus/6730a1000000000000000003/locales/es-ES
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "data": {
    "header": {
      "title": "Menú del día",
      "subtitle": "Incluye bebida"
    },
    "starters": [
      { "_id": "soup", "name": "Sopa del día" },
      { "_id": "salad", "name": "Ensalada mixta" }
    ],
    "mains": [
      { "_id": "chicken", "name": "Pollo a la plancha" },
      { "_id": "pasta", "name": "Pasta con salsa de tomate" }
    ],
    "extras": [{ "_id": "bread-water", "text": "Pan y agua" }]
  },
  "meta": {
    "title": "Menú del día",
    "summary": "Entrante y principal a elegir · 12,90 € I.V.A. incl."
  }
}
```

**Respuesta esperada:**

```json
{
  "message": "ok"
}
```

---

## 6. Localización en-GB (opcional)

```http
PUT /api/menus/6730a1000000000000000003/locales/en-GB
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "data": {
    "header": {
      "title": "Daily Menu",
      "subtitle": "Drink included"
    },
    "starters": [
      { "_id": "soup", "name": "Soup of the day" },
      { "_id": "salad", "name": "Mixed salad" }
    ],
    "mains": [
      { "_id": "chicken", "name": "Grilled chicken" },
      { "_id": "pasta", "name": "Pasta with tomato sauce" }
    ],
    "extras": [{ "_id": "bread-water", "text": "Bread and water" }]
  },
  "meta": {
    "title": "Daily Menu",
    "summary": "Starter and main of your choice · €12.90 VAT incl."
  }
}
```

**Respuesta esperada:**

```json
{
  "message": "ok"
}
```

---

## 7. Publicar Localizaciones

### Publicar es-ES

```http
POST /api/menus/6730a1000000000000000003/publish/es-ES
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

**Respuesta esperada:**

```json
{
  "message": "ok"
}
```

### Publicar en-GB (opcional)

```http
POST /api/menus/6730a1000000000000000003/publish/en-GB
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

**Respuesta esperada:**

```json
{
  "message": "ok"
}
```

---

## 8. Listar Menús Disponibles con Título/Summary (Público)

### Nuevo contrato con metadatos

```http
GET /api/menus/public/available?locale=es-ES&tz=Europe/Madrid
```

**Respuesta esperada:**

```json
{
  "items": [
    {
      "id": "6730a1000000000000000003",
      "name": "Menú diario básico UI",
      "template_slug": "daily-basic-ui",
      "template_version": 1,
      "title": "Menú del día",
      "summary": "Entrante y principal a elegir · 12,90 € I.V.A. incl.",
      "updated_at": "2025-09-01T09:30:00Z"
    }
  ]
}
```

### Con fallback de idioma

```http
GET /api/menus/public/available?locale=fr-FR&fallback=en-GB&tz=Europe/Madrid
```

Si no existe `meta` para `fr-FR`, se resuelve desde `en-GB`:

```json
{
  "items": [
    {
      "id": "6730a1000000000000000003",
      "name": "Menú diario básico UI",
      "template_slug": "daily-basic-ui",
      "template_version": 1,
      "title": "Daily Menu",
      "summary": "Starter and main of your choice · €12.90 VAT incl.",
      "updated_at": "2025-09-01T09:30:00Z"
    }
  ]
}
```

---

## 9. Render Final con UI Manifest (Público)

```http
GET /api/menus/6730a1000000000000000003/render?locale=es-ES&with_ui=1
```

**Respuesta esperada (completa):**

```json
{
  "id": "6730a1000000000000000003",
  "name": "Menú diario básico UI",
  "template": {
    "slug": "daily-basic-ui",
    "version": 1
  },
  "locale": "es-ES",
  "ui": {
    "layout": "sections",
    "sections": [
      {
        "key": "header",
        "role": "header",
        "order": 0,
        "display": "hero",
        "labels": { "es-ES": "Cabecera" }
      },
      {
        "key": "starters",
        "role": "course_list",
        "order": 10,
        "display": "list",
        "labels": { "es-ES": "Entrantes" },
        "hints": {
          "choose_count": 1,
          "scope": "per_person",
          "show_price": false
        }
      },
      {
        "key": "mains",
        "role": "course_list",
        "order": 20,
        "display": "list",
        "labels": { "es-ES": "Platos principales" },
        "hints": {
          "choose_count": 1,
          "scope": "per_person",
          "show_price": false
        }
      },
      {
        "key": "extras",
        "role": "extras",
        "order": 30,
        "display": "bullets",
        "labels": { "es-ES": "Incluye" }
      },
      {
        "key": "footer",
        "role": "price_footer",
        "order": 40,
        "display": "footer_price",
        "labels": { "es-ES": "Precio" }
      }
    ],
    "catalogs": {
      "currency": {
        "code": "EUR",
        "symbol": "€",
        "locale": "es-ES"
      }
    }
  },
  "meta": {
    "title": "Menú del día",
    "summary": "Entrante y principal a elegir · 12,90 € I.V.A. incl."
  },
  "data": {
    "header": {
      "title": "Menú del día",
      "subtitle": "Incluye bebida"
    },
    "starters": [
      { "_id": "soup", "name": "Sopa del día" },
      { "_id": "salad", "name": "Ensalada mixta" }
    ],
    "mains": [
      { "_id": "chicken", "name": "Pollo a la plancha" },
      { "_id": "pasta", "name": "Pasta con salsa de tomate" }
    ],
    "extras": [{ "_id": "bread-water", "text": "Pan y agua" }],
    "footer": {
      "price_total": 12.9,
      "vat_percent": 10,
      "vat_included": true
    }
  }
}
```

### Render en inglés

```http
GET /api/menus/6730a1000000000000000003/render?locale=en-GB&with_ui=1
```

**Respuesta (diferencias clave):**

```json
{
  "locale": "en-GB",
  "ui": {
    "sections": [
      { "key": "header", "labels": { "en-GB": "Header" } },
      { "key": "starters", "labels": { "en-GB": "Starters" } },
      { "key": "mains", "labels": { "en-GB": "Mains" } },
      { "key": "extras", "labels": { "en-GB": "Includes" } },
      { "key": "footer", "labels": { "en-GB": "Price" } }
    ]
  },
  "meta": {
    "title": "Daily Menu",
    "summary": "Starter and main of your choice · €12.90 VAT incl."
  },
  "data": {
    "header": {
      "title": "Daily Menu",
      "subtitle": "Drink included"
    },
    "starters": [
      { "_id": "soup", "name": "Soup of the day" },
      { "_id": "salad", "name": "Mixed salad" }
    ],
    "mains": [
      { "_id": "chicken", "name": "Grilled chicken" },
      { "_id": "pasta", "name": "Pasta with tomato sauce" }
    ]
  }
}
```

---

## 🆕 Nuevas Funcionalidades Implementadas

### **1. Metadatos (Meta)**

- **`meta.title`**: Título para listados públicos
- **`meta.summary`**: Resumen descriptivo con precio
- **Resolución multiidioma**: Con fallback automático
- **Uso en listados**: API `/public/available` incluye título y resumen

### **2. UI Manifest Mejorado**

- **Secciones ordenadas**: Campo `order` para control de layout
- **Hints específicos**: `choose_count`, `scope`, `show_price`
- **Labels multiidioma**: Títulos de sección traducidos
- **Catálogos integrados**: Currency, alérgenos, etc.

### **3. Estructura de Datos Optimizada**

- **Common**: Datos no traducibles (estructura, precios)
- **Locales.data**: Contenido traducible (nombres, textos)
- **Locales.meta**: Metadatos traducibles (título, resumen)

### **4. Endpoints Públicos Mejorados**

- **`/public/available`**: Lista con título y resumen
- **`/render?with_ui=1`**: Incluye UI manifest completo
- **Fallback automático**: Si falta traducción, usa idioma de respaldo

---

## 🎯 Casos de Uso

### **📱 Listado de Menús (Frontend)**

```typescript
// Obtener lista de menús disponibles
const response = await fetch(
  "/api/menus/public/available?locale=es-ES&tz=Europe/Madrid"
);
const { items } = await response.json();

// Mostrar en lista
items.forEach((menu) => {
  console.log(`${menu.title}: ${menu.summary}`);
  // "Menú del día: Entrante y principal a elegir · 12,90 € I.V.A. incl."
});
```

### **🍽️ Renderizado de Menú**

```typescript
// Obtener menú completo con UI
const response = await fetch(
  `/api/menus/${menuId}/render?locale=es-ES&with_ui=1`
);
const menuData = await response.json();

// Renderizar usando UI manifest
<MenuRender payload={menuData} />;
```

### **🌍 Soporte Multiidioma**

```typescript
// Español
GET /render?locale=es-ES
// → "Menú del día", "Entrantes", "Platos principales"

// Inglés
GET /render?locale=en-GB
// → "Daily Menu", "Starters", "Mains"

// Con fallback
GET /render?locale=fr-FR&fallback=en-GB
// → Usa inglés si no existe francés
```

---

## ✨ Beneficios del Nuevo Sistema

### **🔧 Flexibilidad**

- **Templates reutilizables**: Misma estructura, contenido diferente
- **UI agnóstica**: Frontend se adapta automáticamente
- **Metadatos separados**: Título/resumen independientes del contenido

### **🌍 Internacionalización**

- **Multiidioma completo**: Contenido, UI labels y metadatos
- **Fallback inteligente**: Nunca se queda sin traducción
- **Gestión centralizada**: Un lugar para cada idioma

### **⚡ Performance**

- **Listados optimizados**: Solo título y resumen, no todo el contenido
- **Renderizado eficiente**: UI manifest guía la construcción
- **Caching friendly**: Estructura predecible

### **📊 Mantenibilidad**

- **Separación clara**: Common vs locales vs meta
- **Versionado**: Templates versionados independientemente
- **Escalabilidad**: Fácil agregar nuevos campos y secciones

Este sistema proporciona una base sólida para menús diarios simples con capacidades avanzadas de UI y metadatos, manteniendo la flexibilidad para casos más complejos. 🎉
