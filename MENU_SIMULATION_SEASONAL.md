# Simulación de endpoints: seasonal-menu (v3)

Guía paso a paso para crear y publicar una carta estacional (`seasonal-menu` v3) con datos anidados y listas de items, incluyendo requests/responses listos para probar.

## Suposiciones

- Base URL local: `http://localhost:5000`
- Autenticación: JWT Bearer (incluye tu token en `Authorization`)
- Tenant: `aralar`
- Zona horaria: `Europe/Madrid`
- Días disponibles: jueves y viernes
- Fechas de ejemplo: septiembre–diciembre 2025

## 0) Headers comunes

```
Authorization: Bearer <ACCESS_TOKEN_DEL_EDITOR_O_ADMIN>
Content-Type: application/json
```

---

## 1) Crear TEMPLATE (draft)

POST `/api/menu-templates`

Body
```json
{
  "name": "Carta estacional",
  "slug": "seasonal-menu",
  "tenant_id": "aralar",
  "version": 3,
  "status": "draft",
  "i18n": { "default_locale": "es-ES", "locales": ["es-ES", "en-GB"] },
  "sections": [
    {
      "key": "header",
      "label": { "es-ES": "Cabecera", "en-GB": "Header" },
      "repeatable": false,
      "fields": [
        { "key": "title",           "type": "text",      "required": true,  "maxLength": 150, "translatable": true },
        { "key": "subtitle",        "type": "text",      "required": false, "maxLength": 180, "translatable": true },
        { "key": "season_code",     "type": "enum",      "required": true,  "enum": ["spring","summer","autumn","winter"], "translatable": false },
        { "key": "cover_image_alt", "type": "text",      "required": false, "maxLength": 140, "translatable": true }
      ]
    },
    {
      "key": "courses",
      "label": { "es-ES":"Secciones de platos", "en-GB":"Course sections" },
      "repeatable": true,
      "minItems": 1,
      "maxItems": 8,
      "fields": [
        { "key": "_id",          "type": "text", "required": true, "translatable": false },
        { "key": "course_title", "type": "text", "required": true, "translatable": true },
        {
          "key": "items",
          "type": "list",
          "minItems": 1,
          "maxItems": 40,
          "itemSchema": {
            "fields": [
              { "key": "_id",         "type": "text",      "required": true,  "translatable": false },
              { "key": "name",        "type": "text",      "required": true,  "maxLength": 120, "translatable": true },
              { "key": "description", "type": "rich_text", "required": false, "maxLength": 800, "translatable": true },
              { "key": "price",       "type": "price",     "currency": "EUR", "required": true, "translatable": false },
              { "key": "is_vegan",    "type": "boolean",   "required": false, "translatable": false },
              { "key": "image_alt",   "type": "text",      "required": false, "maxLength": 140, "translatable": true },
              { "key": "allergens",   "type": "tags",      "enum": ["gluten","lactose","nuts","fish","eggs","soy"], "required": false, "translatable": false }
            ]
          }
        }
      ]
    },
    {
      "key": "footer",
      "label": { "es-ES":"Notas","en-GB":"Notes" },
      "repeatable": false,
      "fields": [
        { "key":"service_note", "type":"textarea", "required": false, "maxLength": 300, "translatable": true }
      ]
    }
  ],
  "ui": { "layout": "tabs" }
}
```

Respuesta (201)
```json
{ "id": "66f2a1000000000000000001" }
```

---

## 2) Publicar TEMPLATE (v3)

POST `/api/menu-templates/66f2a1000000000000000001/publish`

Body
```json
{ "notes": "Publicación inicial v3" }
```

Respuesta (201)
```json
{ "id": "66f2a1000000000000000002" }
```

---

## 3) Crear MENÚ (draft) con datos comunes

POST `/api/menus`

Body
```json
{
  "tenant_id": "aralar",
  "template_slug": "seasonal-menu",
  "template_version": 3,
  "status": "draft",
  "common": {
    "header": {
      "season_code": "autumn"
    },
    "courses": [
      {
        "_id": "sec-starters",
        "items": [
          { "_id": "dish-gazpacho", "price": 5.5, "is_vegan": true,  "allergens": [] },
          { "_id": "dish-tortilla", "price": 4.2, "is_vegan": false, "allergens": ["eggs"] }
        ]
      },
      {
        "_id": "sec-mains",
        "items": [
          { "_id": "dish-paella", "price": 12.0, "is_vegan": false, "allergens": ["fish"] }
        ]
      }
    ]
  }
}
```

Respuesta (201) (resumen)
```json
{
  "_id": "66f2a1000000000000000003",
  "tenant_id": "aralar",
  "template_slug": "seasonal-menu",
  "template_version": 3,
  "status": "draft",
  "common": { "...como en el body..." },
  "locales": {},
  "publish": {}
}
```

---

## 4) Disponibilidad (JUE/VIE, sep-dic 2025)

PUT `/api/menus/66f2a1000000000000000003/availability`

Body
```json
{
  "timezone": "Europe/Madrid",
  "days_of_week": ["THU","FRI"],
  "date_ranges": [
    { "start": "2025-09-01", "end": "2025-12-31" }
  ]
}
```

Respuesta (200)
```json
{ "message": "ok" }
```

---

## 5) Localización es-ES

PUT `/api/menus/66f2a1000000000000000003/locales/es-ES`

Body
```json
{
  "data": {
    "header": {
      "title": "Carta de Otoño 2025",
      "subtitle": "Ingredientes de temporada",
      "cover_image_alt": "Plato otoñal en mesa rústica"
    },
    "courses": [
      {
        "_id": "sec-starters",
        "course_title": "Entrantes",
        "items": [
          { "_id": "dish-gazpacho", "name": "Gazpacho", "description": "Tomate, pepino y AOVE" },
          { "_id": "dish-tortilla", "name": "Tortilla de patatas", "description": "Clásica con huevos camperos", "image_alt": "Porción de tortilla" }
        ]
      },
      {
        "_id": "sec-mains",
        "course_title": "Platos principales",
        "items": [
          { "_id": "dish-paella", "name": "Paella", "description": "Arroz con mariscos y caldo casero", "image_alt": "Paella recién hecha" }
        ]
      }
    ],
    "footer": { "service_note": "Pan y bebida no incluidos." }
  }
}
```

Respuesta (200)
```json
{ "message": "ok" }
```

---

## 6) Localización en-GB (opcional)

PUT `/api/menus/66f2a1000000000000000003/locales/en-GB`

Body
```json
{
  "data": {
    "header": {
      "title": "Autumn Menu 2025",
      "subtitle": "Seasonal ingredients",
      "cover_image_alt": "Autumn dish on rustic table"
    },
    "courses": [
      {
        "_id": "sec-starters",
        "course_title": "Starters",
        "items": [
          { "_id": "dish-gazpacho", "name": "Gazpacho", "description": "Tomato, cucumber & EVOO" },
          { "_id": "dish-tortilla", "name": "Spanish omelette", "description": "Classic with free-range eggs", "image_alt": "Slice of omelette" }
        ]
      },
      {
        "_id": "sec-mains",
        "course_title": "Mains",
        "items": [
          { "_id": "dish-paella", "name": "Paella", "description": "Rice with seafood and house stock", "image_alt": "Freshly cooked paella" }
        ]
      }
    ],
    "footer": { "service_note": "Bread and drink not included." }
  }
}
```

Respuesta (200)
```json
{ "message": "ok" }
```

---

## 7) Publicar locales

POST `/api/menus/66f2a1000000000000000003/publish/es-ES`

Respuesta (200)
```json
{ "message": "ok" }
```

Opcional

POST `/api/menus/66f2a1000000000000000003/publish/en-GB`

Respuesta (200)
```json
{ "message": "ok" }
```

---

## 7.1) Validar si el menú está listo para publicación global
GET `/api/menus/66f2a1000000000000000003/validate`
Respuesta (200)
```json
{ "message": "ok" }
```

Si faltan requisitos, devuelve:
```json
{ "message": "invalid", "issues": ["availability is required", "at least one locale must be published"] }
```

## 7.2) Publicar MENÚ (estado global)
POST `/api/menus/66f2a1000000000000000003/publish`
Respuesta (200)
```json
{ "message": "ok" }
```

Si faltan requisitos, responde 409 con mensaje describiendo los issues.

## 7.3) (Opcional) Despublicar MENÚ
POST `/api/menus/66f2a1000000000000000003/unpublish`
Respuesta (200)
```json
{ "message": "ok" }
```

Nota: Para que un menú aparezca en público se requiere:
- `status` del menú igual a `published`, y
- al menos un locale publicado (p. ej., `publish.es-ES.status = "published"`), y
- una disponibilidad que incluya el día consultado.

---

## 8) (Público) Menús disponibles en una fecha

GET `/api/menus/public/available?locale=es-ES&tz=Europe/Madrid&date=2025-09-05`

Respuesta (200)
```json
{
  "items": [
    {
      "id": "66f2a1000000000000000003",
      "template_slug": "seasonal-menu",
      "template_version": 3,
      "updated_at": "2025-09-01T09:30:00Z"
    }
  ]
}
```

> Si llamas sin `date`, usa “hoy” en la TZ dada: `&tz=Europe/Madrid`.

---

## 9) (Público) Render final (JSON fusionado) — es-ES

GET `/api/menus/66f2a1000000000000000003/render?locale=es-ES`

Respuesta (200)
```json
{
  "id": "66f2a1000000000000000003",
  "tenant_id": "aralar",
  "template": { "slug": "seasonal-menu", "version": 3 },
  "locale": "es-ES",
  "fallback_used": null,
  "published_at": "2025-09-01T10:00:00Z",
  "updated_at": "2025-09-01T09:30:00Z",
  "data": {
    "header": {
      "title": "Carta de Otoño 2025",
      "subtitle": "Ingredientes de temporada",
      "season_code": "autumn",
      "cover_image_alt": "Plato otoñal en mesa rústica"
    },
    "courses": [
      {
        "_id": "sec-starters",
        "course_title": "Entrantes",
        "items": [
          { "_id": "dish-gazpacho", "name": "Gazpacho", "description": "Tomate, pepino y AOVE", "price": 5.5, "is_vegan": true,  "allergens": [] },
          { "_id": "dish-tortilla", "name": "Tortilla de patatas", "description": "Clásica con huevos camperos", "image_alt": "Porción de tortilla", "price": 4.2, "is_vegan": false, "allergens": ["eggs"] }
        ]
      },
      {
        "_id": "sec-mains",
        "course_title": "Platos principales",
        "items": [
          { "_id": "dish-paella", "name": "Paella", "description": "Arroz con mariscos y caldo casero", "image_alt": "Paella recién hecha", "price": 12.0, "is_vegan": false, "allergens": ["fish"] }
        ]
      }
    ],
    "footer": { "service_note": "Pan y bebida no incluidos." }
  }
}
```

---

## 10) (Público) Render final — en-GB (si publicaste EN)

GET `/api/menus/66f2a1000000000000000003/render?locale=en-GB`

Respuesta (200)
```json
{
  "id": "66f2a1000000000000000003",
  "tenant_id": "aralar",
  "template": { "slug": "seasonal-menu", "version": 3 },
  "locale": "en-GB",
  "fallback_used": null,
  "published_at": "2025-09-05T10:00:00Z",
  "updated_at": "2025-09-01T09:30:00Z",
  "data": {
    "header": {
      "title": "Autumn Menu 2025",
      "subtitle": "Seasonal ingredients",
      "season_code": "autumn",
      "cover_image_alt": "Autumn dish on rustic table"
    },
    "courses": [
      {
        "_id": "sec-starters",
        "course_title": "Starters",
        "items": [
          { "_id": "dish-gazpacho", "name": "Gazpacho", "description": "Tomato, cucumber & EVOO", "price": 5.5, "is_vegan": true,  "allergens": [] },
          { "_id": "dish-tortilla", "name": "Spanish omelette", "description": "Classic with free-range eggs", "image_alt": "Slice of omelette", "price": 4.2, "is_vegan": false, "allergens": ["eggs"] }
        ]
      },
      {
        "_id": "sec-mains",
        "course_title": "Mains",
        "items": [
          { "_id": "dish-paella", "name": "Paella", "description": "Rice with seafood and house stock", "image_alt": "Freshly cooked paella", "price": 12.0, "is_vegan": false, "allergens": ["fish"] }
        ]
      }
    ],
    "footer": { "service_note": "Bread and drink not included." }
  }
}
```

---

## (Opcional) cURL de arranque

> Cambia `TOKEN` e IDs según tus respuestas reales.

```bash
# 1) Create template (seasonal-menu v3)
curl -X POST http://localhost:5000/api/menu-templates \
 -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
 -d '{ "name":"Carta estacional", "slug":"seasonal-menu", "tenant_id":"aralar", "version":3, "status":"draft", "i18n":{"default_locale":"es-ES","locales":["es-ES","en-GB"]}, "sections":[{"key":"header","label":{"es-ES":"Cabecera","en-GB":"Header"},"repeatable":false,"fields":[{"key":"title","type":"text","required":true,"maxLength":150,"translatable":true},{"key":"subtitle","type":"text","required":false,"maxLength":180,"translatable":true},{"key":"season_code","type":"enum","required":true,"enum":["spring","summer","autumn","winter"],"translatable":false},{"key":"cover_image_alt","type":"text","required":false,"maxLength":140,"translatable":true}]},{"key":"courses","label":{"es-ES":"Secciones de platos","en-GB":"Course sections"},"repeatable":true,"minItems":1,"maxItems":8,"fields":[{"key":"_id","type":"text","required":true,"translatable":false},{"key":"course_title","type":"text","required":true,"translatable":true},{"key":"items","type":"list","minItems":1,"maxItems":40,"itemSchema":{"fields":[{"key":"_id","type":"text","required":true,"translatable":false},{"key":"name","type":"text","required":true,"maxLength":120,"translatable":true},{"key":"description","type":"rich_text","required":false,"maxLength":800,"translatable":true},{"key":"price","type":"price","currency":"EUR","required":true,"translatable":false},{"key":"is_vegan","type":"boolean","required":false,"translatable":false},{"key":"image_alt","type":"text","required":false,"maxLength":140,"translatable":true},{"key":"allergens","type":"tags","enum":["gluten","lactose","nuts","fish","eggs","soy"],"required":false,"translatable":false}]}}]},{"key":"footer","label":{"es-ES":"Notas","en-GB":"Notes"},"repeatable":false,"fields":[{"key":"service_note","type":"textarea","required":false,"maxLength":300,"translatable":true}]}], "ui":{"layout":"tabs"} }'
```
