# Simulación de endpoints: daily-basic

Guía paso a paso para crear y publicar un menú sencillo (`daily-basic`) y simular las peticiones tal como vendrían del frontend.

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
  "name": "Menú del día básico",
  "slug": "daily-basic",
  "tenant_id": "aralar",
  "version": 1,
  "status": "draft",
  "i18n": { "default_locale": "es-ES", "locales": ["es-ES", "en-GB"] },
  "sections": [
    {
      "key": "header",
      "label": { "es-ES": "Cabecera", "en-GB": "Header" },
      "repeatable": false,
      "fields": [
        { "key": "title", "type": "text", "label": {"es-ES":"Título","en-GB":"Title"}, "required": true, "maxLength": 100, "translatable": true },
        { "key": "date",  "type": "date", "label": {"es-ES":"Fecha","en-GB":"Date"}, "required": true, "translatable": false }
      ]
    },
    {
      "key": "items",
      "label": { "es-ES": "Platos", "en-GB": "Dishes" },
      "repeatable": true,
      "minItems": 1,
      "maxItems": 5,
      "fields": [
        { "key": "_id",  "type": "text", "required": true, "translatable": false },
        { "key": "name", "type": "text", "required": true, "maxLength": 120, "translatable": true },
        { "key": "price","type": "price","currency":"EUR","required": true, "translatable": false }
      ]
    }
  ],
  "ui": { "layout": "sections" }
}
```

Respuesta (201)
```json
{ "id": "64f1a1111111111111111111" }
```

> Guarda este `template_id`.

---

## 2) Publicar TEMPLATE (v1)

POST `/api/menu-templates/64f1a1111111111111111111/publish`

Body (opcional)
```json
{ "notes": "Primera publicación v1" }
```

Respuesta (201)
```json
{ "id": "64f1a1222222222222222222" }
```

Este nuevo id corresponde a la versión publicada del slug `daily-basic` con `version: 1`.

---

## 3) Crear MENÚ basado en el template publicado

POST `/api/menus`

Body
```json
{
  "tenant_id": "aralar",
  "template_slug": "daily-basic",
  "template_version": 1,
  "status": "draft",
  "common": {
    "header": { "date": "2025-09-05" },
    "items": [
      { "_id": "dish-gazpacho", "price": 5.5 },
      { "_id": "dish-tortilla", "price": 4.2 }
    ]
  }
}
```

Respuesta (201) (resumen)
```json
{
  "_id": "64f1a1333333333333333333",
  "tenant_id": "aralar",
  "template_id": "64f1a1222222222222222222",
  "template_slug": "daily-basic",
  "template_version": 1,
  "status": "draft",
  "common": {
    "header": { "date": "2025-09-05" },
    "items": [
      { "_id": "dish-gazpacho", "price": 5.5 },
      { "_id": "dish-tortilla", "price": 4.2 }
    ]
  },
  "locales": {},
  "publish": {}
}
```

> Guarda este `menu_id`: `64f1a1333333333333333333`.

---

## 4) Configurar disponibilidad

PUT `/api/menus/64f1a1333333333333333333/availability`

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

## 5) Agregar traducción ES (localizable)

PUT `/api/menus/64f1a1333333333333333333/locales/es-ES`

Body
```json
{
  "data": {
    "header": { "title": "Menú del día" },
    "items": [
      { "_id": "dish-gazpacho", "name": "Gazpacho" },
      { "_id": "dish-tortilla", "name": "Tortilla de patatas" }
    ]
  }
}
```

Respuesta (200)
```json
{ "message": "ok" }
```

---

## 6) (Opcional) Agregar traducción EN

PUT `/api/menus/64f1a1333333333333333333/locales/en-GB`

Body
```json
{
  "data": {
    "header": { "title": "Daily Menu" },
    "items": [
      { "_id": "dish-gazpacho", "name": "Gazpacho" },
      { "_id": "dish-tortilla", "name": "Spanish omelette" }
    ]
  }
}
```

Respuesta (200)
```json
{ "message": "ok" }
```

---

## 7) Publicar el locale ES

POST `/api/menus/64f1a1333333333333333333/publish/es-ES`

Respuesta (200)
```json
{ "message": "ok" }
```

> Si quieres publicar EN más tarde, repite `POST /publish/en-GB`.

---

## 8) (Público) Consultar menús disponibles hoy

GET `/api/menus/public/available?locale=es-ES&tz=Europe/Madrid`

Respuesta (200)
```json
{
  "items": [
    {
      "id": "64f1a1333333333333333333",
      "template_slug": "daily-basic",
      "template_version": 1,
      "updated_at": "2025-09-01T09:30:00Z"
    }
  ]
}
```

> Si hoy no es jueves ni viernes en `Europe/Madrid`, esta lista estará vacía.
> Prueba con una fecha específica (p. ej., viernes 2025-09-05):

GET `/api/menus/public/available?locale=es-ES&tz=Europe/Madrid&date=2025-09-05`

---

## 9) (Público) Renderizar el menú final (JSON fusionado) 🇪🇸

GET `/api/menus/64f1a1333333333333333333/render?locale=es-ES`

Respuesta (200) (ejemplo)
```json
{
  "id": "64f1a1333333333333333333",
  "tenant_id": "aralar",
  "template": { "slug": "daily-basic", "version": 1 },
  "locale": "es-ES",
  "fallback_used": null,
  "published_at": "2025-09-01T10:00:00Z",
  "updated_at": "2025-09-01T09:30:00Z",
  "data": {
    "header": {
      "title": "Menú del día",
      "date": "2025-09-05"
    },
    "items": [
      { "_id": "dish-gazpacho", "name": "Gazpacho", "price": 5.5 },
      { "_id": "dish-tortilla", "name": "Tortilla de patatas", "price": 4.2 }
    ]
  }
}
```

> Si ES no estuviera publicado pero EN sí, podrías usar:
> `/render?locale=es-ES&fallback=en-GB` → devolverá datos en EN y `fallback_used: "en-GB"`.

---

## (Opcional) cURL de ejemplo (rápido)

> Cambia `TOKEN` y los IDs según tus respuestas reales.

```bash
# 1) Create template
curl -X POST http://localhost:5000/api/menu-templates \
 -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
 -d '{ "name":"Menú del día básico", "slug":"daily-basic", "tenant_id":"aralar", "version":1, "status":"draft", "i18n":{"default_locale":"es-ES","locales":["es-ES","en-GB"]}, "sections":[{"key":"header","label":{"es-ES":"Cabecera","en-GB":"Header"},"repeatable":false,"fields":[{"key":"title","type":"text","required":true,"translatable":true},{"key":"date","type":"date","required":true,"translatable":false}]},{"key":"items","label":{"es-ES":"Platos","en-GB":"Dishes"},"repeatable":true,"fields":[{"key":"_id","type":"text","required":true,"translatable":false},{"key":"name","type":"text","required":true,"translatable":true},{"key":"price","type":"price","currency":"EUR","required":true,"translatable":false}]}] }'
```
