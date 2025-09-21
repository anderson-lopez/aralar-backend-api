# Simulación de endpoints: seasonal-autumn (v1)

Guía paso a paso para crear y publicar una carta estacional de otoño con múltiples secciones, imágenes y catálogo completo de alérgenos. Incluye entrantes, platos principales, postres, vinos de temporada y disponibilidad estacional.

## Suposiciones

- Base URL local: `http://localhost:5000`
- Autenticación: JWT Bearer (incluye tu token en `Authorization`)
- Tenant: `aralar`
- Zona horaria: `Europe/Madrid`
- El template `seasonal-autumn` v1 se creará y publicará en este proceso.

## 0) Headers comunes

```
Authorization: Bearer <ACCESS_TOKEN_DEL_EDITOR_O_ADMIN>
Content-Type: application/json
```

---

## 0) (Front) Pedir presign y subir archivos

### Banner principal

POST `/api/uploads/presign`

Body

```json
{
  "filename": "banner-otono.webp",
  "mime": "image/webp",
  "folder": "menus/banners"
}
```

Respuesta (200)

```json
{
  "upload_url": "<URL_PUT_FIRMADA>",
  "public_url": "https://cdn.example.com/menus/banners/uuid-banner-otono.webp",
  "key": "menus/banners/uuid-banner-otono.webp"
}
```

### Imágenes de platos

Repite el proceso para cada imagen de plato:

- `ensalada-templada.webp`
- `setas-salteadas.webp`
- `carrillera.webp`
- `bacalao.webp`
- `tarta-queso.webp`
- `vino-crianza.webp`

Todas en la carpeta `menus/items`.

---

## 1) Crear TEMPLATE (draft)

POST `/api/menu-templates`

Body

```json
{
  "name": "Carta Estacional Otoño (Vinos y Platos)",
  "slug": "seasonal-autumn",
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
        },
        {
          "key": "banner_image",
          "type": "image",
          "required": true,
          "translatable": false
        },
        {
          "key": "banner_image_alt",
          "type": "text",
          "required": false,
          "translatable": true,
          "maxLength": 140
        }
      ],
      "ui": { "role": "header", "order": 0, "display": "hero" }
    },
    {
      "key": "starters",
      "label": { "es-ES": "Entrantes", "en-GB": "Starters" },
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
        },
        {
          "key": "description",
          "type": "textarea",
          "required": false,
          "translatable": true
        },
        {
          "key": "allergens",
          "type": "tags",
          "required": false,
          "translatable": false,
          "enum": [
            "gluten",
            "crustaceans",
            "eggs",
            "fish",
            "peanuts",
            "soy",
            "milk",
            "nuts",
            "celery",
            "mustard",
            "sesame",
            "sulfites",
            "lupin",
            "molluscs"
          ]
        },
        {
          "key": "image",
          "type": "image",
          "required": false,
          "translatable": false
        },
        {
          "key": "image_alt",
          "type": "text",
          "required": false,
          "translatable": true,
          "maxLength": 140
        }
      ],
      "ui": {
        "role": "course_list",
        "order": 10,
        "display": "list",
        "hints": { "show_price": false }
      }
    },
    {
      "key": "mains",
      "label": { "es-ES": "Platos principales", "en-GB": "Mains" },
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
        },
        {
          "key": "description",
          "type": "textarea",
          "required": false,
          "translatable": true
        },
        {
          "key": "allergens",
          "type": "tags",
          "required": false,
          "translatable": false,
          "enum": [
            "gluten",
            "crustaceans",
            "eggs",
            "fish",
            "peanuts",
            "soy",
            "milk",
            "nuts",
            "celery",
            "mustard",
            "sesame",
            "sulfites",
            "lupin",
            "molluscs"
          ]
        },
        {
          "key": "image",
          "type": "image",
          "required": false,
          "translatable": false
        },
        {
          "key": "image_alt",
          "type": "text",
          "required": false,
          "translatable": true,
          "maxLength": 140
        }
      ],
      "ui": {
        "role": "course_list",
        "order": 20,
        "display": "list",
        "hints": { "show_price": false }
      }
    },
    {
      "key": "desserts",
      "label": { "es-ES": "Postres", "en-GB": "Desserts" },
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
        },
        {
          "key": "allergens",
          "type": "tags",
          "required": false,
          "translatable": false,
          "enum": ["gluten", "eggs", "milk", "nuts", "sesame", "sulfites"]
        },
        {
          "key": "image",
          "type": "image",
          "required": false,
          "translatable": false
        },
        {
          "key": "image_alt",
          "type": "text",
          "required": false,
          "translatable": true,
          "maxLength": 140
        }
      ],
      "ui": {
        "role": "course_list",
        "order": 30,
        "display": "grid",
        "hints": { "show_price": false, "icon": "cupcake" }
      }
    },
    {
      "key": "wines",
      "label": { "es-ES": "Vinos de temporada", "en-GB": "Seasonal wines" },
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
        },
        {
          "key": "description",
          "type": "textarea",
          "required": false,
          "translatable": true
        },
        {
          "key": "image",
          "type": "image",
          "required": false,
          "translatable": false
        },
        {
          "key": "image_alt",
          "type": "text",
          "required": false,
          "translatable": true,
          "maxLength": 140
        }
      ],
      "ui": {
        "role": "course_list",
        "order": 40,
        "display": "grid",
        "hints": { "show_price": false, "icon": "wine" }
      }
    },
    {
      "key": "footer",
      "label": { "es-ES": "Precio", "en-GB": "Price" },
      "repeatable": false,
      "fields": [
        {
          "key": "note",
          "type": "text",
          "required": false,
          "translatable": true
        }
      ],
      "ui": { "role": "price_footer", "order": 90, "display": "footer_price" }
    }
  ],
  "ui": {
    "layout": "sections",
    "catalogs": {
      "allergens": [
        { "code": "gluten", "icon": "agluten" },
        { "code": "crustaceans", "icon": "acrusta" },
        { "code": "eggs", "icon": "aegg" },
        { "code": "fish", "icon": "afish" },
        { "code": "peanuts", "icon": "apeanut" },
        { "code": "soy", "icon": "asoy" },
        { "code": "milk", "icon": "amilk" },
        { "code": "nuts", "icon": "anuts" },
        { "code": "celery", "icon": "acelery" },
        { "code": "mustard", "icon": "amustard" },
        { "code": "sesame", "icon": "asesame" },
        { "code": "sulfites", "icon": "asulfite" },
        { "code": "lupin", "icon": "alupin" },
        { "code": "molluscs", "icon": "amollusc" }
      ],
      "currency": { "code": "EUR", "symbol": "€", "locale": "es-ES" }
    }
  }
}
```

Respuesta (201)

```json
{ "id": "6740a1000000000000000001" }
```

---

## 2) Publicar TEMPLATE

POST `/api/menu-templates/6740a1000000000000000001/publish`

Body

```json
{ "notes": "v1 publicada" }
```

Respuesta (201)

```json
{ "id": "6740a1000000000000000002" }
```

> Guarda `template_id = "6740a1000000000000000002"`.

---

## 3) Crear MENÚ (draft)

POST `/api/menus`

Body

```json
{
  "tenant_id": "aralar",
  "template_slug": "seasonal-autumn",
  "template_version": 1,
  "status": "draft",
  "common": {
    "header": {
      "banner_image": {
        "url": "https://cdn.example.com/menus/banners/uuid-banner-otono.webp",
        "mime": "image/webp",
        "width": 1920,
        "height": 860,
        "size": 380000
      }
    },
    "starters": [
      {
        "_id": "ensalada-templada",
        "allergens": ["nuts", "milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-ensalada-templada.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 210000
        }
      },
      {
        "_id": "setas-salteadas",
        "allergens": ["milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-setas.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 205000
        }
      }
    ],
    "mains": [
      {
        "_id": "carrillera-vino-tinto",
        "allergens": ["sulfites", "milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-carrillera.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 230000
        }
      },
      {
        "_id": "bacalao-al-pilpil",
        "allergens": ["fish", "milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-bacalao.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 215000
        }
      }
    ],
    "desserts": [
      {
        "_id": "tarta-de-queso",
        "allergens": ["milk", "eggs"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-cheesecake.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 190000
        }
      },
      {
        "_id": "peras-al-vino",
        "allergens": ["sulfites"]
      }
    ],
    "wines": [
      {
        "_id": "crianza-rioja",
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-crianza.webp",
          "mime": "image/webp",
          "width": 1000,
          "height": 1400,
          "size": 180000
        }
      },
      {
        "_id": "blanco-txakoli"
      }
    ],
    "footer": {}
  }
}
```

Respuesta (201)

```json
{
  "_id": "6740a1000000000000000003",
  "tenant_id": "aralar",
  "template_slug": "seasonal-autumn",
  "template_version": 1,
  "status": "draft",
  "common": {
    "header": {
      "banner_image": {
        "url": "https://cdn.example.com/menus/banners/uuid-banner-otono.webp",
        "mime": "image/webp",
        "width": 1920,
        "height": 860,
        "size": 380000
      }
    },
    "starters": [
      {
        "_id": "ensalada-templada",
        "allergens": ["nuts", "milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-ensalada-templada.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 210000
        }
      },
      {
        "_id": "setas-salteadas",
        "allergens": ["milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-setas.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 205000
        }
      }
    ],
    "mains": [
      {
        "_id": "carrillera-vino-tinto",
        "allergens": ["sulfites", "milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-carrillera.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 230000
        }
      },
      {
        "_id": "bacalao-al-pilpil",
        "allergens": ["fish", "milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-bacalao.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 215000
        }
      }
    ],
    "desserts": [
      {
        "_id": "tarta-de-queso",
        "allergens": ["milk", "eggs"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-cheesecake.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 190000
        }
      },
      { "_id": "peras-al-vino", "allergens": ["sulfites"] }
    ],
    "wines": [
      {
        "_id": "crianza-rioja",
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-crianza.webp",
          "mime": "image/webp",
          "width": 1000,
          "height": 1400,
          "size": 180000
        }
      },
      { "_id": "blanco-txakoli" }
    ],
    "footer": {}
  },
  "locales": {},
  "publish": {}
}
```

> Guarda `menu_id = "6740a1000000000000000003"`.

---

## 4) Disponibilidad (estacional)

PUT `/api/menus/6740a1000000000000000003/availability`

Body

```json
{
  "timezone": "Europe/Madrid",
  "days_of_week": ["THU", "FRI", "SAT", "SUN"],
  "date_ranges": [{ "start": "2025-09-20", "end": "2025-12-15" }]
}
```

Respuesta (200)

```json
{ "message": "ok" }
```

---

## 5) Locales ES y EN

PUT `/api/menus/6740a1000000000000000003/locales/es-ES`

Body

```json
{
  "data": {
    "header": {
      "title": "Carta Estacional de Otoño",
      "subtitle": "Sabores de temporada y bodega seleccionada",
      "banner_image_alt": "Mesa otoñal con platos de temporada"
    },
    "starters": [
      {
        "_id": "ensalada-templada",
        "name": "Ensalada templada de frutos secos y queso",
        "description": "Brotes, frutos secos tostados y queso suave."
      },
      {
        "_id": "setas-salteadas",
        "name": "Setas de temporada salteadas",
        "description": "Ajo, perejil y toque de mantequilla",
        "image_alt": "Setas salteadas con hierbas"
      }
    ],
    "mains": [
      {
        "_id": "carrillera-vino-tinto",
        "name": "Carrillera al vino tinto",
        "description": "Guiso lento con puré cremoso"
      },
      {
        "_id": "bacalao-al-pilpil",
        "name": "Bacalao al pil-pil",
        "description": "Clásico emulsionado con aceite y ajo"
      }
    ],
    "desserts": [
      {
        "_id": "tarta-de-queso",
        "name": "Tarta de queso",
        "image_alt": "Porción de tarta de queso cremosa"
      },
      {
        "_id": "peras-al-vino",
        "name": "Peras al vino"
      }
    ],
    "wines": [
      {
        "_id": "crianza-rioja",
        "name": "Rioja Crianza",
        "description": "Fruta madura, vainilla sutil"
      },
      {
        "_id": "blanco-txakoli",
        "name": "Txakoli blanco",
        "description": "Fresco, notas cítricas"
      }
    ],
    "footer": { "note": "Consultar alérgenos con el personal de sala" }
  },
  "meta": {
    "title": "Carta de Otoño",
    "summary": "Platos de temporada y selección de vinos"
  }
}
```

PUT `/api/menus/6740a1000000000000000003/locales/en-GB`

Body

```json
{
  "data": {
    "header": {
      "title": "Autumnal Menu",
      "subtitle": "Seasonal flavors and selected wines",
      "banner_image_alt": "Autumnal table with seasonal dishes"
    },
    "starters": [
      {
        "_id": "ensalada-templada",
        "name": "Tempered Salad of dried fruits and cheese",
        "description": "Broccoli, dried fruits toasted and soft cheese."
      },
      {
        "_id": "setas-salteadas",
        "name": "Seasonal mushrooms sautéed",
        "description": "Garlic, parsley and butter touch",
        "image_alt": "Sautéed mushrooms with herbs"
      }
    ],
    "mains": [
      {
        "_id": "carrillera-vino-tinto",
        "name": "Carrillera with red wine",
        "description": "Slow-cooked stew with creamy puree"
      },
      {
        "_id": "bacalao-al-pilpil",
        "name": "Bacalao pil-pil",
        "description": "Classic emulsion with oil and garlic"
      }
    ],
    "desserts": [
      {
        "_id": "tarta-de-queso",
        "name": "Cheese tart",
        "image_alt": "Portion of creamy cheese tart"
      },
      {
        "_id": "peras-al-vino",
        "name": "Pears with wine"
      }
    ],
    "wines": [
      {
        "_id": "crianza-rioja",
        "name": "Rioja crianza",
        "description": "Fruit ripe, subtle vanilla"
      },
      {
        "_id": "blanco-txakoli",
        "name": "White txakoli",
        "description": "Fresh, citrus notes"
      }
    ],
    "footer": { "note": "Consult allergens with waitstaff" }
  },
  "meta": {
    "title": "Autumn Menu",
    "summary": "Seasonal dishes and wine selection"
  }
}
```

---

## 6) Publicar locales

POST `/api/menus/6740a1000000000000000003/publish/es-ES`

POST `/api/menus/6740a1000000000000000003/publish/en-GB`

Respuestas (200)

```json
{ "message": "ok" }
```

---

## 7) (Público) Menús disponibles hoy

GET `/api/menus/public/available?locale=es-ES&tz=Europe/Madrid`

Respuesta (200)

```json
{
  "items": [
    {
      "id": "6740a1000000000000000003",
      "template_slug": "seasonal-autumn",
      "template_version": 1,
      "title": "Carta de Otoño",
      "summary": "Platos de temporada y selección de vinos",
      "updated_at": "2025-09-20T10:00:00Z"
    }
  ]
}
```

> Si hoy no es jueves, viernes, sábado o domingo en `Europe/Madrid`, esta lista estará vacía.
> Prueba con una fecha específica (p. ej., sábado 2025-09-21):

GET `/api/menus/public/available?locale=es-ES&tz=Europe/Madrid&date=2025-09-21`

---

## 8) (Público) Render final ES

GET `/api/menus/6740a1000000000000000003/render?locale=es-ES`

Respuesta (200)

```json
{
  "id": "6740a1000000000000000003",
  "tenant_id": "aralar",
  "template": { "slug": "seasonal-autumn", "version": 1 },
  "locale": "es-ES",
  "fallback_used": null,
  "published_at": "2025-09-20T10:00:00Z",
  "updated_at": "2025-09-20T09:30:00Z",
  "meta": {
    "title": "Carta de Otoño",
    "summary": "Platos de temporada y selección de vinos"
  },
  "data": {
    "header": {
      "title": "Carta Estacional de Otoño",
      "subtitle": "Sabores de temporada y bodega seleccionada",
      "banner_image": {
        "url": "https://cdn.example.com/menus/banners/uuid-banner-otono.webp",
        "mime": "image/webp",
        "width": 1920,
        "height": 860,
        "size": 380000
      },
      "banner_image_alt": "Mesa otoñal con platos de temporada"
    },
    "starters": [
      {
        "_id": "ensalada-templada",
        "name": "Ensalada templada de frutos secos y queso",
        "description": "Brotes, frutos secos tostados y queso suave.",
        "allergens": ["nuts", "milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-ensalada-templada.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 210000
        }
      },
      {
        "_id": "setas-salteadas",
        "name": "Setas de temporada salteadas",
        "description": "Ajo, perejil y toque de mantequilla",
        "allergens": ["milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-setas.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 205000
        },
        "image_alt": "Setas salteadas con hierbas"
      }
    ],
    "mains": [
      {
        "_id": "carrillera-vino-tinto",
        "name": "Carrillera al vino tinto",
        "description": "Guiso lento con puré cremoso",
        "allergens": ["sulfites", "milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-carrillera.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 230000
        }
      },
      {
        "_id": "bacalao-al-pilpil",
        "name": "Bacalao al pil-pil",
        "description": "Clásico emulsionado con aceite y ajo",
        "allergens": ["fish", "milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-bacalao.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 215000
        }
      }
    ],
    "desserts": [
      {
        "_id": "tarta-de-queso",
        "name": "Tarta de queso",
        "allergens": ["milk", "eggs"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-cheesecake.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 190000
        },
        "image_alt": "Porción de tarta de queso cremosa"
      },
      {
        "_id": "peras-al-vino",
        "name": "Peras al vino",
        "allergens": ["sulfites"]
      }
    ],
    "wines": [
      {
        "_id": "crianza-rioja",
        "name": "Rioja Crianza",
        "description": "Fruta madura, vainilla sutil",
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-crianza.webp",
          "mime": "image/webp",
          "width": 1000,
          "height": 1400,
          "size": 180000
        }
      },
      {
        "_id": "blanco-txakoli",
        "name": "Txakoli blanco",
        "description": "Fresco, notas cítricas"
      }
    ],
    "footer": {
      "note": "Consultar alérgenos con el personal de sala"
    }
  }
}
```

### Con UI Manifest (with_ui=1)

GET `/api/menus/6740a1000000000000000003/render?locale=es-ES&with_ui=1`

Respuesta (200) con UI manifest completo:

```json
{
  "id": "6740a1000000000000000003",
  "tenant_id": "aralar",
  "template": { "slug": "seasonal-autumn", "version": 1 },
  "locale": "es-ES",
  "fallback_used": null,
  "published_at": "2025-09-20T10:00:00Z",
  "updated_at": "2025-09-20T09:30:00Z",
  "ui": {
    "layout": "sections",
    "sections": [
      {
        "key": "header",
        "role": "header",
        "order": 0,
        "display": "hero",
        "labels": { "es-ES": "Cabecera", "en-GB": "Header" }
      },
      {
        "key": "starters",
        "role": "course_list",
        "order": 10,
        "display": "list",
        "labels": { "es-ES": "Entrantes", "en-GB": "Starters" },
        "hints": { "show_price": false }
      },
      {
        "key": "mains",
        "role": "course_list",
        "order": 20,
        "display": "list",
        "labels": { "es-ES": "Platos principales", "en-GB": "Mains" },
        "hints": { "show_price": false }
      },
      {
        "key": "desserts",
        "role": "course_list",
        "order": 30,
        "display": "grid",
        "labels": { "es-ES": "Postres", "en-GB": "Desserts" },
        "hints": { "show_price": false, "icon": "cupcake" }
      },
      {
        "key": "wines",
        "role": "course_list",
        "order": 40,
        "display": "grid",
        "labels": { "es-ES": "Vinos de temporada", "en-GB": "Seasonal wines" },
        "hints": { "show_price": false, "icon": "wine" }
      },
      {
        "key": "footer",
        "role": "price_footer",
        "order": 90,
        "display": "footer_price",
        "labels": { "es-ES": "Precio", "en-GB": "Price" }
      }
    ],
    "catalogs": {
      "allergens": [
        { "code": "gluten", "icon": "agluten" },
        { "code": "crustaceans", "icon": "acrusta" },
        { "code": "eggs", "icon": "aegg" },
        { "code": "fish", "icon": "afish" },
        { "code": "peanuts", "icon": "apeanut" },
        { "code": "soy", "icon": "asoy" },
        { "code": "milk", "icon": "amilk" },
        { "code": "nuts", "icon": "anuts" },
        { "code": "celery", "icon": "acelery" },
        { "code": "mustard", "icon": "amustard" },
        { "code": "sesame", "icon": "asesame" },
        { "code": "sulfites", "icon": "asulfite" },
        { "code": "lupin", "icon": "alupin" },
        { "code": "molluscs", "icon": "amollusc" }
      ],
      "currency": { "code": "EUR", "symbol": "€", "locale": "es-ES" }
    }
  },
  "meta": {
    "title": "Carta de Otoño",
    "summary": "Platos de temporada y selección de vinos"
  },
  "data": {
    "header": {
      "title": "Carta Estacional de Otoño",
      "subtitle": "Sabores de temporada y bodega seleccionada",
      "banner_image": {
        "url": "https://cdn.example.com/menus/banners/uuid-banner-otono.webp",
        "mime": "image/webp",
        "width": 1920,
        "height": 860,
        "size": 380000
      },
      "banner_image_alt": "Mesa otoñal con platos de temporada"
    },
    "starters": [
      {
        "_id": "ensalada-templada",
        "name": "Ensalada templada de frutos secos y queso",
        "description": "Brotes, frutos secos tostados y queso suave.",
        "allergens": ["nuts", "milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-ensalada-templada.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 210000
        }
      },
      {
        "_id": "setas-salteadas",
        "name": "Setas de temporada salteadas",
        "description": "Ajo, perejil y toque de mantequilla",
        "allergens": ["milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-setas.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 205000
        },
        "image_alt": "Setas salteadas con hierbas"
      }
    ],
    "mains": [
      {
        "_id": "carrillera-vino-tinto",
        "name": "Carrillera al vino tinto",
        "description": "Guiso lento con puré cremoso",
        "allergens": ["sulfites", "milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-carrillera.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 230000
        }
      },
      {
        "_id": "bacalao-al-pilpil",
        "name": "Bacalao al pil-pil",
        "description": "Clásico emulsionado con aceite y ajo",
        "allergens": ["fish", "milk"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-bacalao.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 215000
        }
      }
    ],
    "desserts": [
      {
        "_id": "tarta-de-queso",
        "name": "Tarta de queso",
        "allergens": ["milk", "eggs"],
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-cheesecake.webp",
          "mime": "image/webp",
          "width": 1200,
          "height": 900,
          "size": 190000
        },
        "image_alt": "Porción de tarta de queso cremosa"
      },
      {
        "_id": "peras-al-vino",
        "name": "Peras al vino",
        "allergens": ["sulfites"]
      }
    ],
    "wines": [
      {
        "_id": "crianza-rioja",
        "name": "Rioja Crianza",
        "description": "Fruta madura, vainilla sutil",
        "image": {
          "url": "https://cdn.example.com/menus/items/uuid-crianza.webp",
          "mime": "image/webp",
          "width": 1000,
          "height": 1400,
          "size": 180000
        }
      },
      {
        "_id": "blanco-txakoli",
        "name": "Txakoli blanco",
        "description": "Fresco, notas cítricas"
      }
    ],
    "footer": {
      "note": "Consultar alérgenos con el personal de sala"
    }
  }
}
```

---

## (Opcional) cURL de ejemplo (rápido)

> Cambia `TOKEN` y los IDs según tus respuestas reales.

```bash
# Create seasonal-autumn menu (draft)
curl -X POST http://localhost:5000/api/menus \
 -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
 -d '{ "tenant_id":"aralar","template_slug":"seasonal-autumn","template_version":1,"status":"draft","common":{"header":{"banner_image":{"url":"https://cdn.example.com/menus/banners/uuid-banner-otono.webp","mime":"image/webp","width":1920,"height":860,"size":380000}},"starters":[{"_id":"ensalada-templada","allergens":["nuts","milk"],"image":{"url":"https://cdn.example.com/menus/items/uuid-ensalada-templada.webp","mime":"image/webp","width":1200,"height":900,"size":210000}},{"_id":"setas-salteadas","allergens":["milk"],"image":{"url":"https://cdn.example.com/menus/items/uuid-setas.webp","mime":"image/webp","width":1200,"height":900,"size":205000}}],"mains":[{"_id":"carrillera-vino-tinto","allergens":["sulfites","milk"],"image":{"url":"https://cdn.example.com/menus/items/uuid-carrillera.webp","mime":"image/webp","width":1200,"height":900,"size":230000}},{"_id":"bacalao-al-pilpil","allergens":["fish","milk"],"image":{"url":"https://cdn.example.com/menus/items/uuid-bacalao.webp","mime":"image/webp","width":1200,"height":900,"size":215000}}],"desserts":[{"_id":"tarta-de-queso","allergens":["milk","eggs"],"image":{"url":"https://cdn.example.com/menus/items/uuid-cheesecake.webp","mime":"image/webp","width":1200,"height":900,"size":190000}},{"_id":"peras-al-vino","allergens":["sulfites"]}],"wines":[{"_id":"crianza-rioja","image":{"url":"https://cdn.example.com/menus/items/uuid-crianza.webp","mime":"image/webp","width":1000,"height":1400,"size":180000}},{"_id":"blanco-txakoli"}],"footer":{}}}'
```

---

## 🆕 Nuevas Funcionalidades Implementadas

### **1. Template Complejo Multi-Sección**

Este template demuestra un menú completo con múltiples tipos de secciones:

- **Header**: Banner hero con título y subtítulo
- **Starters**: Entrantes con imágenes y descripciones
- **Mains**: Platos principales con alérgenos
- **Desserts**: Postres en layout grid con icono cupcake
- **Wines**: Vinos de temporada en grid con icono wine
- **Footer**: Nota informativa sobre alérgenos

### **2. Catálogo Completo de Alérgenos**

Incluye los 14 alérgenos principales de la UE:

- **Cereales con gluten**, **crustáceos**, **huevos**, **pescado**
- **cacahuetes**, **soja**, **leche**, **frutos secos**
- **apio**, **mostaza**, **sésamo**, **sulfitos**, **altramuces**, **moluscos**

### **3. UI Hints Avanzados**

- **`show_price: false`**: Carta sin precios (menú degustación)
- **`icon: "cupcake"`**: Icono específico para postres
- **`icon: "wine"`**: Icono específico para vinos
- **`display: "grid"`**: Layout en cuadrícula para elementos visuales

### **4. Disponibilidad Estacional**

- **Días específicos**: Jueves a domingo (THU, FRI, SAT, SUN)
- **Rango temporal**: Temporada otoñal (sep-dic)
- **Flexibilidad**: Fácil adaptación a otras temporadas

### **5. Estructura de Datos Optimizada**

- **Common**: Imágenes, alérgenos y estructura técnica
- **Locales**: Textos traducibles y metadatos por idioma
- **Meta**: Título y resumen para listados públicos
- **UI**: Configuración completa de renderizado

---

## 🎯 Beneficios del Sistema Estacional

### **🍂 Gestión Temporal**

- Menús que aparecen/desaparecen automáticamente por temporada
- Disponibilidad configurable por días de la semana
- Perfecto para ofertas especiales y eventos

### **🍷 Contenido Rico**

- Soporte completo para vinos y maridajes
- Descripciones detalladas y evocativas
- Imágenes optimizadas para cada elemento

### **⚠️ Seguridad Alimentaria**

- Catálogo completo de alérgenos UE
- Información clara y accesible
- Cumplimiento normativo automático

### **🎨 Experiencia Visual**

- Layouts diferenciados por tipo de contenido
- Iconos contextuales (cupcake, wine)
- Banner hero para impacto visual

### **🌍 Multiidioma Completo**

- Traducciones independientes por sección
- Metadatos localizados para SEO
- Fallback inteligente entre idiomas

Este sistema proporciona una base robusta para menús estacionales complejos, manteniendo la flexibilidad y escalabilidad del sistema base. 🎉
