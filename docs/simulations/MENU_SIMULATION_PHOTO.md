# Simulación de endpoints: simple-photo (v1)

Guía paso a paso para crear y publicar un menú con imágenes presignadas (`simple-photo` v1). Incluye validación, publicación global y despublicación.

## Suposiciones

- Base URL local: `http://localhost:5000`
- Autenticación: JWT Bearer (incluye tu token en `Authorization`)
- Tenant: `aralar`
- Zona horaria: `Europe/Madrid`
- El template `simple-photo` v1 ya está publicado (si no, créalo/publica antes).

## 0) Headers comunes

```
Authorization: Bearer <ACCESS_TOKEN_DEL_EDITOR_O_ADMIN>
Content-Type: application/json
```

---

## 0) (Front) pedir presign y subir archivos (banner + 1 foto de plato)

POST `/api/uploads/presign`

Body
```json
{ "filename": "banner.webp", "mime": "image/webp", "folder": "menus/banners" }
```

Respuesta (200)
```json
{
  "upload_url": "<URL_PUT_FIRMADA>",
  "public_url": "https://cdn.example.com/menus/banners/uuid-banner.webp",
  "key": "menus/banners/uuid-banner.webp"
}
```

El frontend hace PUT binario a `upload_url`.

Repite para plato:

POST `/api/uploads/presign`

Body
```json
{ "filename": "ensalada.webp", "mime": "image/webp", "folder": "menus/dishes" }
```

Respuesta (200)
```json
{
  "upload_url": "<URL_PUT_FIRMADA>",
  "public_url": "https://cdn.example.com/menus/dishes/uuid-ensalada.webp",
  "key": "menus/dishes/uuid-ensalada.webp"
}
```

---

## 1) Crear TEMPLATE (draft)

POST `/api/menu-templates`

Body
```json
{
  "name": "Menú sencillo con fotos",
  "slug": "simple-photo",
  "tenant_id": "aralar",
  "version": 1,
  "status": "draft",
  "i18n": { "default_locale": "es-ES", "locales": ["es-ES","en-GB"] },
  "sections": [
    {
      "key": "header",
      "label": { "es-ES": "Cabecera", "en-GB": "Header" },
      "repeatable": false,
      "fields": [
        { "key": "title", "type": "text", "required": true, "translatable": true },
        { "key": "banner_image", "type": "image", "required": true, "translatable": false }
      ],
      "ui": {
        "role": "header",
        "order": 0,
        "display": "hero"
      }
    },
    {
      "key": "dishes",
      "label": { "es-ES": "Platos", "en-GB": "Dishes" },
      "repeatable": true,
      "fields": [
        { "key": "_id", "type": "text", "required": true, "translatable": false },
        { "key": "name", "type": "text", "required": true, "translatable": true },
        { "key": "price", "type": "price", "currency": "EUR", "required": true, "translatable": false },
        { "key": "image", "type": "image", "required": false, "translatable": false },
        { "key": "image_alt", "type": "text", "required": false, "translatable": true, "maxLength": 140 }
      ],
      "ui": {
        "role": "course_list",
        "order": 10,
        "display": "grid",
        "hints": {
          "show_price": true
        }
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

Respuesta (201)
```json
{ "id": "6710a1000000000000000001" }
```

---

## 2) Publicar TEMPLATE

POST `/api/menu-templates/6710a1000000000000000001/publish`

Body
```json
{ "notes": "v1 publicada" }
```

Respuesta (201)
```json
{ "id": "6710a1000000000000000002" }
```

---

## 3) Crear MENÚ (draft) usando las public_url de presign

POST `/api/menus`

Body
```json
{
  "tenant_id": "aralar",
  "name": "Menú sencillo con fotos",
  "template_slug": "simple-photo",
  "template_version": 1,
  "status": "draft",
  "common": {
    "header": {
      "banner_image": {
        "url": "https://cdn.example.com/menus/banners/uuid-banner.webp",
        "mime": "image/webp",
        "width": 1600,
        "height": 600,
        "size": 210000
      }
    },
    "dishes": [
      {
        "_id": "dish-ensalada",
        "price": 6.0,
        "image": {
          "url": "https://cdn.example.com/menus/dishes/uuid-ensalada.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 180000
        }
      },
      { "_id": "dish-sopa", "price": 5.0 }
    ]
  }
}
```

Respuesta (201)
```json
{ "_id": "6710a1000000000000000003", "tenant_id": "aralar", "name": "Menú sencillo con fotos", "template_slug": "simple-photo", "template_version": 1, "status": "draft", "common": { "header": { "banner_image": { "url": "https://cdn.example.com/menus/banners/uuid-banner.webp", "mime": "image/webp", "width": 1600, "height": 600, "size": 210000 } }, "dishes": [ { "_id": "dish-ensalada", "price": 6.0, "image": { "url": "https://cdn.example.com/menus/dishes/uuid-ensalada.webp", "mime": "image/webp", "width": 1200, "height": 900, "size": 180000 } }, { "_id": "dish-sopa", "price": 5.0 } ] }, "locales": {}, "publish": {} }
```

> Guarda `menu_id = "6710a1000000000000000003"`.

---

## 4) Disponibilidad (JUE/VIE sep–dic)

PUT `/api/menus/6710a1000000000000000003/availability`

Body
```json
{
  "timezone": "Europe/Madrid",
  "days_of_week": ["THU","FRI"],
  "date_ranges": [{ "start": "2025-09-01", "end": "2025-12-31" }]
}
```

Respuesta (200)
```json
{ "message": "ok" }
```

---

## 5) Locales ES y EN (títulos y ALT)

PUT `/api/menus/6710a1000000000000000003/locales/es-ES`

Body
```json
{
  "data": {
    "header": { "title": "Menú sencillo con fotos" },
    "dishes": [
      { "_id": "dish-ensalada", "name": "Ensalada fresca", "image_alt": "Ensalada con ingredientes de temporada" },
      { "_id": "dish-sopa", "name": "Sopa del día" }
    ]
  },
  "meta": {
    "title": "Menú sencillo con fotos",
    "summary": "Ensalada fresca y sopa del día · 11,00 € I.V.A. incl."
  }
}
```

PUT `/api/menus/6710a1000000000000000003/locales/en-GB`

Body
```json
{
  "data": {
    "header": { "title": "Simple photo menu" },
    "dishes": [
      { "_id": "dish-ensalada", "name": "Fresh salad", "image_alt": "Seasonal ingredient salad" },
      { "_id": "dish-sopa", "name": "Soup of the day" }
    ]
  },
  "meta": {
    "title": "Simple photo menu",
    "summary": "Fresh salad and soup of the day · €11.00 VAT incl."
  }
}
```

Respuestas (200)
```json
{ "message": "ok" }
```

---

## 6) Publicar locales

POST `/api/menus/6710a1000000000000000003/publish/es-ES`

POST `/api/menus/6710a1000000000000000003/publish/en-GB`

Respuestas (200)
```json
{ "message": "ok" }
```

---

## 6.1) Validar si el menú está listo para publicación global

GET `/api/menus/6710a1000000000000000003/validate`

Respuesta (200)
```json
{ "message": "ok" }
```

Si faltan requisitos, devuelve:
```json
{ "message": "invalid", "issues": ["availability is required", "at least one locale must be published"] }
```

---

## 6.2) Publicar MENÚ (estado global)

POST `/api/menus/6710a1000000000000000003/publish`

Respuesta (200)
```json
{ "message": "ok" }
```

Si faltan requisitos, responde 409 con el detalle de `issues`.

---

## 6.3) (Opcional) Despublicar MENÚ

POST `/api/menus/6710a1000000000000000003/unpublish`

Respuesta (200)
```json
{ "message": "ok" }
```

> Nota: Para aparecer en público se requiere `status = "published"`, al menos un locale publicado y disponibilidad válida para la fecha consultada.

---

## 7) (Público) Menús disponibles hoy

GET `/api/menus/public/available?locale=es-ES&tz=Europe/Madrid`

Respuesta (200)
```json
{
  "items": [
    {
      "id": "6710a1000000000000000003",
      "name": "Menú sencillo con fotos",
      "template_slug": "simple-photo",
      "template_version": 1,
      "title": "Menú sencillo con fotos",
      "summary": "Ensalada fresca y sopa del día · 11,00 € I.V.A. incl.",
      "updated_at": "2025-09-01T09:30:00Z"
    }
  ]
}
```

---

## 8) (Público) Render final ES

GET `/api/menus/6710a1000000000000000003/render?locale=es-ES`

Respuesta (200)
```json
{
  "id": "6710a1000000000000000003",
  "name": "Menú sencillo con fotos",
  "template": { "slug": "simple-photo", "version": 1 },
  "locale": "es-ES",
  "meta": {
    "title": "Menú sencillo con fotos",
    "summary": "Ensalada fresca y sopa del día · 11,00 € I.V.A. incl."
  },
  "data": {
    "header": {
      "title": "Menú sencillo con fotos",
      "banner_image": {
        "url": "https://cdn.example.com/menus/banners/uuid-banner.webp",
        "mime": "image/webp",
        "width": 1600,
        "height": 600,
        "size": 210000
      }
    },
    "dishes": [
      {
        "_id": "dish-ensalada",
        "name": "Ensalada fresca",
        "price": 6.0,
        "image": {
          "url": "https://cdn.example.com/menus/dishes/uuid-ensalada.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 180000
        },
        "image_alt": "Ensalada con ingredientes de temporada"
      },
      { "_id": "dish-sopa", "name": "Sopa del día", "price": 5.0 }
    ]
  }
}
```

### Con UI Manifest (with_ui=1)

GET `/api/menus/6710a1000000000000000003/render?locale=es-ES&with_ui=1`

Respuesta (200) con UI manifest completo:
```json
{
  "id": "6710a1000000000000000003",
  "name": "Menú sencillo con fotos",
  "template": { "slug": "simple-photo", "version": 1 },
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
        "key": "dishes",
        "role": "course_list",
        "order": 10,
        "display": "grid",
        "labels": { "es-ES": "Platos" },
        "hints": {
          "show_price": true
        }
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
    "title": "Menú sencillo con fotos",
    "summary": "Ensalada fresca y sopa del día · 11,00 € I.V.A. incl."
  },
  "data": {
    "header": {
      "title": "Menú sencillo con fotos",
      "banner_image": {
        "url": "https://cdn.example.com/menus/banners/uuid-banner.webp",
        "mime": "image/webp",
        "width": 1600,
        "height": 600,
        "size": 210000
      }
    },
    "dishes": [
      {
        "_id": "dish-ensalada",
        "name": "Ensalada fresca",
        "price": 6.0,
        "image": {
          "url": "https://cdn.example.com/menus/dishes/uuid-ensalada.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 180000
        },
        "image_alt": "Ensalada con ingredientes de temporada"
      },
      { "_id": "dish-sopa", "name": "Sopa del día", "price": 5.0 }
    ]
  }
}
```

---

## (Opcional) cURL de arranque

> Cambia `TOKEN` e IDs según tus respuestas reales.

```bash
# Create simple-photo menu (draft)
curl -X POST http://localhost:5000/api/menus \
 -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
 -d '{ "tenant_id":"aralar","name":"Menú sencillo con fotos","template_slug":"simple-photo","template_version":1,"status":"draft","common":{"header":{"banner_image":{"url":"https://cdn.example.com/menus/banners/uuid-banner.webp","mime":"image/webp","width":1600,"height":600,"size":210000}},"dishes":[{"_id":"dish-ensalada","price":6.0,"image":{"url":"https://cdn.example.com/menus/dishes/uuid-ensalada.webp","mime":"image/webp","width":1200,"height":900,"size":180000}},{"_id":"dish-sopa","price":5.0}]}}'
```

---

## 🆕 Nuevas Funcionalidades Implementadas

### **1. UI Properties por Sección**

Cada sección del template ahora incluye propiedades `ui`:

- **Header**: `role: "header"`, `order: 0`, `display: "hero"` - Ideal para banners con imágenes
- **Dishes**: `role: "course_list"`, `order: 10`, `display: "grid"` - Layout en cuadrícula para mostrar imágenes de platos
- **`hints.show_price`**: Controla si se muestran los precios en la UI

### **2. Metadatos (Meta) con Imágenes**

Las localizaciones incluyen metadatos optimizados para menús con fotos:

- **`meta.title`**: Título descriptivo para listados
- **`meta.summary`**: Resumen con precios totales y descripción del contenido
- **Multiidioma**: Metadatos traducibles independientes del contenido visual

### **3. UI Manifest para Contenido Visual**

El template incluye configuración específica para menús con imágenes:

- **`display: "grid"`**: Layout optimizado para mostrar imágenes de platos
- **`display: "hero"`**: Header con banner de imagen destacada
- **Catálogos de currency**: Información de moneda para precios

### **4. Endpoints Mejorados para Contenido Visual**

- **`/public/available`**: Incluye título y resumen para preview sin cargar imágenes
- **`/render?with_ui=1`**: UI manifest completo con instrucciones de layout para imágenes
- **Optimización de carga**: Metadatos ligeros para listados, contenido completo para renderizado

### **5. Estructura Optimizada para Imágenes**

- **Common**: URLs de imágenes, dimensiones y metadatos técnicos
- **Locales.data**: Textos alternativos (alt) traducibles para accesibilidad
- **Locales.meta**: Títulos y resúmenes traducibles para SEO y listados

---

## 🎯 Beneficios para Menús con Imágenes

### **📸 Gestión de Imágenes Optimizada**
- URLs presignadas para subida segura de imágenes
- Metadatos técnicos (dimensiones, tamaño, MIME) incluidos
- Textos alternativos traducibles para accesibilidad

### **🎨 UI Responsiva y Atractiva**
- Layout en cuadrícula para mostrar platos con imágenes
- Header hero para banners impactantes
- Configuración flexible de visualización de precios

### **⚡ Performance Optimizada**
- Listados ligeros con solo título y resumen
- Carga progresiva: metadatos primero, imágenes después
- UI manifest guía el renderizado eficiente

### **🌍 Accesibilidad y SEO**
- Textos alternativos traducibles para imágenes
- Metadatos estructurados para mejor indexación
- Soporte completo multiidioma incluyendo descripciones visuales

### **🔧 Integración con CDN**
- URLs públicas optimizadas para CDN
- Soporte para múltiples formatos de imagen (WebP, JPEG, PNG)
- Metadatos técnicos para optimización automática

Este sistema proporciona una base sólida para menús con contenido visual rico, manteniendo la performance y accesibilidad mientras ofrece una experiencia de usuario atractiva. 🎉
