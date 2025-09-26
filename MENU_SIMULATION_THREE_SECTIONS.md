# Simulación de endpoints: three-sections-multiimages (v1)

Documentación completa del template **three-sections-multiimages** que demuestra un menú con 3 secciones (entrantes, pescados y carnes, postre y café) donde cada plato puede tener múltiples imágenes con textos alternativos localizados.

## Características del Template

- **3 secciones principales**: Entrantes, Pescados y carnes, Postre y café
- **Múltiples imágenes por plato**: Array `images[]` con metadatos completos
- **Textos alternativos localizados**: Array `images_alt[]` traducible por idioma
- **Alérgenos específicos**: Catálogo completo UE con enum por sección
- **Layout grid**: Visualización optimizada para contenido visual
- **Sin precios**: Enfoque en presentación gastronómica

## Suposiciones

- **Servidor**: `http://localhost:5000`
- **Headers comunes**: `Authorization: Bearer TOKEN`, `Content-Type: application/json`
- **Tenant**: `aralar`
- **Idiomas**: `es-ES` (principal), `en-GB` (opcional)

---

## 0) Presign y subida de imágenes

### Múltiples imágenes por plato

```bash
# Croquetas (2 imágenes)
POST /api/uploads/presign
{ "filename":"croquetas-1.webp","mime":"image/webp","folder":"menus/items" }
POST /api/uploads/presign  
{ "filename":"croquetas-2.webp","mime":"image/webp","folder":"menus/items" }

# Pulpo (2 imágenes)
POST /api/uploads/presign
{ "filename":"pulpo-1.webp","mime":"image/webp","folder":"menus/items" }
POST /api/uploads/presign
{ "filename":"pulpo-2.webp","mime":"image/webp","folder":"menus/items" }

# Merluza (1 imagen)
POST /api/uploads/presign
{ "filename":"merluza-1.webp","mime":"image/webp","folder":"menus/items" }

# Entrecot (2 imágenes)  
POST /api/uploads/presign
{ "filename":"entrecot-1.webp","mime":"image/webp","folder":"menus/items" }
POST /api/uploads/presign
{ "filename":"entrecot-2.webp","mime":"image/webp","folder":"menus/items" }

# Tarta de queso (1 imagen)
POST /api/uploads/presign
{ "filename":"tarta-queso-1.webp","mime":"image/webp","folder":"menus/items" }
```

> Cada respuesta incluye `upload_url` (PUT) y `public_url`. Guarda las public_url para el paso 4.

---

## 1) Crear TEMPLATE (draft)

POST `/api/menu-templates`

```json
{
  "name": "Carta 3 secciones (entrantes, pescados y carnes, postre y café)",
  "slug": "three-sections-multiimages",
  "tenant_id": "aralar",
  "version": 1,
  "status": "draft",
  "i18n": { 
    "default_locale": "es-ES", 
    "locales": ["es-ES", "en-GB"] 
  },
  "sections": [
    {
      "key": "starters",
      "label": { "es-ES": "Entrantes", "en-GB": "Starters" },
      "repeatable": true,
      "fields": [
        { "key": "_id", "type": "text", "required": true, "translatable": false },
        { "key": "name", "type": "text", "required": true, "translatable": true },
        { 
          "key": "allergens", 
          "type": "tags", 
          "required": false, 
          "translatable": false,
          "enum": ["gluten","crustaceans","eggs","fish","peanuts","soy","milk","nuts","celery","mustard","sesame","sulfites","lupin","molluscs"] 
        },
        {
          "key": "images",
          "type": "list",
          "required": false,
          "translatable": false,
          "itemSchema": {
            "fields": [
              { "key": "url", "type": "text", "required": true, "translatable": false },
              { "key": "mime", "type": "text", "required": true, "translatable": false },
              { "key": "width", "type": "number", "required": false, "translatable": false },
              { "key": "height", "type": "number", "required": false, "translatable": false },
              { "key": "size", "type": "number", "required": false, "translatable": false }
            ]
          }
        },
        { "key": "images_alt", "type": "list", "required": false, "translatable": true }
      ],
      "ui": { 
        "role": "course_list", 
        "order": 10, 
        "display": "grid", 
        "hints": { "show_price": false } 
      }
    },
    {
      "key": "fish_meat",
      "label": { "es-ES": "Pescados y carnes", "en-GB": "Fish & Meat" },
      "repeatable": true,
      "fields": [
        { "key": "_id", "type": "text", "required": true, "translatable": false },
        { "key": "name", "type": "text", "required": true, "translatable": true },
        { 
          "key": "allergens", 
          "type": "tags", 
          "required": false, 
          "translatable": false,
          "enum": ["gluten","crustaceans","eggs","fish","peanuts","soy","milk","nuts","celery","mustard","sesame","sulfites","lupin","molluscs"] 
        },
        {
          "key": "images",
          "type": "list",
          "required": false,
          "translatable": false,
          "itemSchema": {
            "fields": [
              { "key": "url", "type": "text", "required": true, "translatable": false },
              { "key": "mime", "type": "text", "required": true, "translatable": false },
              { "key": "width", "type": "number", "required": false, "translatable": false },
              { "key": "height", "type": "number", "required": false, "translatable": false },
              { "key": "size", "type": "number", "required": false, "translatable": false }
            ]
          }
        },
        { "key": "images_alt", "type": "list", "required": false, "translatable": true }
      ],
      "ui": { 
        "role": "course_list", 
        "order": 20, 
        "display": "grid", 
        "hints": { "show_price": false } 
      }
    },
    {
      "key": "dessert_coffee",
      "label": { "es-ES": "Postre y café", "en-GB": "Dessert & Coffee" },
      "repeatable": true,
      "fields": [
        { "key": "_id", "type": "text", "required": true, "translatable": false },
        { "key": "name", "type": "text", "required": true, "translatable": true },
        { 
          "key": "allergens", 
          "type": "tags", 
          "required": false, 
          "translatable": false,
          "enum": ["gluten","eggs","milk","nuts","sesame","sulfites"] 
        },
        {
          "key": "images",
          "type": "list",
          "required": false,
          "translatable": false,
          "itemSchema": {
            "fields": [
              { "key": "url", "type": "text", "required": true, "translatable": false },
              { "key": "mime", "type": "text", "required": true, "translatable": false },
              { "key": "width", "type": "number", "required": false, "translatable": false },
              { "key": "height", "type": "number", "required": false, "translatable": false },
              { "key": "size", "type": "number", "required": false, "translatable": false }
            ]
          }
        },
        { "key": "images_alt", "type": "list", "required": false, "translatable": true }
      ],
      "ui": { 
        "role": "course_list", 
        "order": 30, 
        "display": "grid", 
        "hints": { "show_price": false, "icon": "cupcake" } 
      }
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
{ "id": "6750a1000000000000000001" }
```

---

## 2) Publicar TEMPLATE

POST `/api/menu-templates/6750a1000000000000000001/publish`

```json
{ "notes": "v1: tres secciones con múltiples imágenes por plato" }
```

Respuesta (201)
```json
{ "id": "6750a1000000000000000002" }
```

---

## 3) Crear MENÚ (draft)

POST `/api/menus`

```json
{
  "tenant_id": "aralar",
  "template_slug": "three-sections-multiimages",
  "template_version": 1,
  "status": "draft",
  "common": {
    "starters": [
      {
        "_id": "croquetas-jamon",
        "allergens": ["gluten", "eggs", "milk"],
        "images": [
          {
            "url": "https://cdn.example.com/menus/items/croquetas-1.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 180000
          },
          {
            "url": "https://cdn.example.com/menus/items/croquetas-2.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 175000
          }
        ]
      },
      {
        "_id": "pulpo-gallega",
        "allergens": [],
        "images": [
          {
            "url": "https://cdn.example.com/menus/items/pulpo-1.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 190000
          },
          {
            "url": "https://cdn.example.com/menus/items/pulpo-2.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 185000
          }
        ]
      }
    ],
    "fish_meat": [
      {
        "_id": "merluza-plancha",
        "allergens": ["fish"],
        "images": [
          {
            "url": "https://cdn.example.com/menus/items/merluza-1.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 200000
          }
        ]
      },
      {
        "_id": "entrecot-plancha",
        "allergens": [],
        "images": [
          {
            "url": "https://cdn.example.com/menus/items/entrecot-1.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 210000
          },
          {
            "url": "https://cdn.example.com/menus/items/entrecot-2.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 205000
          }
        ]
      }
    ],
    "dessert_coffee": [
      {
        "_id": "tarta-queso",
        "allergens": ["milk", "eggs"],
        "images": [
          {
            "url": "https://cdn.example.com/menus/items/tarta-queso-1.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 195000
          }
        ]
      },
      {
        "_id": "cafe-solo",
        "allergens": []
      }
    ]
  }
}
```

Respuesta (201)
```json
{ "id": "6750a1000000000000000003" }
```

---

## 4) Configurar disponibilidad

PUT `/api/menus/6750a1000000000000000003/availability`

```json
{
  "timezone": "Europe/Madrid",
  "days_of_week": ["THU", "FRI", "SAT"],
  "date_ranges": [{ "start": "2025-09-25", "end": "2025-12-31" }]
}
```

Respuesta (200)
```json
{ "message": "ok" }
```

---

## 5) Locale ES con textos e images_alt

PUT `/api/menus/6750a1000000000000000003/locales/es-ES`

```json
{
  "data": {
    "starters": [
      {
        "_id": "croquetas-jamon",
        "name": "Croquetas de jamón",
        "images_alt": ["Croquetas crujientes", "Detalle interior cremoso"]
      },
      {
        "_id": "pulpo-gallega",
        "name": "Pulpo a la gallega",
        "images_alt": ["Plato de pulpo con pimentón", "Detalle de rodajas de pulpo"]
      }
    ],
    "fish_meat": [
      {
        "_id": "merluza-plancha",
        "name": "Merluza a la plancha",
        "images_alt": ["Merluza con guarnición de verduras"]
      },
      {
        "_id": "entrecot-plancha",
        "name": "Entrecot a la plancha",
        "images_alt": ["Entrecot al punto", "Corte del entrecot"]
      }
    ],
    "dessert_coffee": [
      {
        "_id": "tarta-queso",
        "name": "Tarta de queso",
        "images_alt": ["Porción de tarta de queso"]
      },
      {
        "_id": "cafe-solo",
        "name": "Café solo"
      }
    ]
  },
  "meta": {
    "title": "Carta — 3 secciones",
    "summary": "Entrantes, pescados y carnes, postre y café"
  }
}
```

Respuesta (200)
```json
{ "message": "ok" }
```

---

## 6) Locale EN (opcional)

PUT `/api/menus/6750a1000000000000000003/locales/en-GB`

```json
{
  "data": {
    "starters": [
      {
        "_id": "croquetas-jamon",
        "name": "Ham Croquettes",
        "images_alt": ["Crispy croquettes", "Creamy interior detail"]
      },
      {
        "_id": "pulpo-gallega",
        "name": "Galician-style Octopus",
        "images_alt": ["Octopus dish with paprika", "Octopus slices detail"]
      }
    ],
    "fish_meat": [
      {
        "_id": "merluza-plancha",
        "name": "Grilled Hake",
        "images_alt": ["Hake with vegetable garnish"]
      },
      {
        "_id": "entrecot-plancha",
        "name": "Grilled Ribeye",
        "images_alt": ["Medium-rare ribeye", "Ribeye cut"]
      }
    ],
    "dessert_coffee": [
      {
        "_id": "tarta-queso",
        "name": "Cheesecake",
        "images_alt": ["Cheesecake slice"]
      },
      {
        "_id": "cafe-solo",
        "name": "Black Coffee"
      }
    ]
  },
  "meta": {
    "title": "Menu — 3 Sections",
    "summary": "Starters, fish & meat, dessert & coffee"
  }
}
```

---

## 7) Publicar locales

POST `/api/menus/6750a1000000000000000003/publish/es-ES`

Respuesta (200)
```json
{ "message": "ok" }
```

POST `/api/menus/6750a1000000000000000003/publish/en-GB`

Respuesta (200)
```json
{ "message": "ok" }
```

---

## 8) (Público) Menús disponibles

GET `/api/menus/public/available?locale=es-ES&tz=Europe/Madrid`

Respuesta (200)
```json
{
  "items": [
    {
      "id": "6750a1000000000000000003",
      "template_slug": "three-sections-multiimages",
      "template_version": 1,
      "title": "Carta — 3 secciones",
      "summary": "Entrantes, pescados y carnes, postre y café",
      "updated_at": "2025-09-25T10:00:00Z"
    }
  ]
}
```

> Si hoy no es jueves, viernes o sábado en `Europe/Madrid`, esta lista estará vacía.
> Prueba con una fecha específica (p. ej., sábado 2025-09-27):

GET `/api/menus/public/available?locale=es-ES&tz=Europe/Madrid&date=2025-09-27`

---

## 9) (Público) Render final ES

GET `/api/menus/6750a1000000000000000003/render?locale=es-ES`

Respuesta (200)
```json
{
  "id": "6750a1000000000000000003",
  "tenant_id": "aralar",
  "template": { "slug": "three-sections-multiimages", "version": 1 },
  "locale": "es-ES",
  "fallback_used": null,
  "published_at": "2025-09-25T10:00:00Z",
  "updated_at": "2025-09-25T09:30:00Z",
  "meta": {
    "title": "Carta — 3 secciones",
    "summary": "Entrantes, pescados y carnes, postre y café"
  },
  "data": {
    "starters": [
      {
        "_id": "croquetas-jamon",
        "name": "Croquetas de jamón",
        "allergens": ["gluten", "eggs", "milk"],
        "images": [
          {
            "url": "https://cdn.example.com/menus/items/croquetas-1.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 180000
          },
          {
            "url": "https://cdn.example.com/menus/items/croquetas-2.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 175000
          }
        ],
        "images_alt": ["Croquetas crujientes", "Detalle interior cremoso"]
      },
      {
        "_id": "pulpo-gallega",
        "name": "Pulpo a la gallega",
        "allergens": [],
        "images": [
          {
            "url": "https://cdn.example.com/menus/items/pulpo-1.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 190000
          },
          {
            "url": "https://cdn.example.com/menus/items/pulpo-2.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 185000
          }
        ],
        "images_alt": ["Plato de pulpo con pimentón", "Detalle de rodajas de pulpo"]
      }
    ],
    "fish_meat": [
      {
        "_id": "merluza-plancha",
        "name": "Merluza a la plancha",
        "allergens": ["fish"],
        "images": [
          {
            "url": "https://cdn.example.com/menus/items/merluza-1.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 200000
          }
        ],
        "images_alt": ["Merluza con guarnición de verduras"]
      },
      {
        "_id": "entrecot-plancha",
        "name": "Entrecot a la plancha",
        "allergens": [],
        "images": [
          {
            "url": "https://cdn.example.com/menus/items/entrecot-1.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 210000
          },
          {
            "url": "https://cdn.example.com/menus/items/entrecot-2.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 205000
          }
        ],
        "images_alt": ["Entrecot al punto", "Corte del entrecot"]
      }
    ],
    "dessert_coffee": [
      {
        "_id": "tarta-queso",
        "name": "Tarta de queso",
        "allergens": ["milk", "eggs"],
        "images": [
          {
            "url": "https://cdn.example.com/menus/items/tarta-queso-1.webp",
            "mime": "image/webp",
            "width": 1200,
            "height": 900,
            "size": 195000
          }
        ],
        "images_alt": ["Porción de tarta de queso"]
      },
      {
        "_id": "cafe-solo",
        "name": "Café solo",
        "allergens": []
      }
    ]
  }
}
```

### Con UI Manifest (with_ui=1)

GET `/api/menus/6750a1000000000000000003/render?locale=es-ES&with_ui=1`

> La respuesta incluye el UI manifest completo con las 3 secciones ordenadas, catálogo de alérgenos y configuración de currency. Ver ejemplo anterior con el campo `ui` añadido.

---

## 🆕 Nuevas Funcionalidades Implementadas

### **1. Múltiples Imágenes por Plato**

Este template demuestra el manejo avanzado de imágenes:

- **Array `images[]`**: Cada plato puede tener múltiples imágenes
- **Metadatos completos**: url, mime, width, height, size por imagen
- **Flexibilidad**: Desde 0 imágenes (café solo) hasta múltiples por plato

### **2. Textos Alternativos Localizados**

- **Array `images_alt[]`**: Textos alternativos por índice de imagen
- **Traducible**: Diferentes textos por idioma
- **Accesibilidad**: Cumplimiento WCAG para lectores de pantalla
- **SEO**: Mejora la indexación de imágenes

### **3. Estructura Gastronómica Clásica**

- **Entrantes**: Aperitivos y primeros platos
- **Pescados y carnes**: Platos principales diferenciados
- **Postre y café**: Finalización de la comida
- **Alérgenos específicos**: Enum adaptado por sección

### **4. Layout Grid Optimizado**

- **Display grid**: Visualización en cuadrícula para todas las secciones
- **Sin precios**: Enfoque en presentación visual
- **Icono cupcake**: Identificación visual para postres
- **Responsive**: Adaptación automática a diferentes pantallas

### **5. Gestión de Contenido Visual**

- **Presign múltiple**: Subida eficiente de varias imágenes
- **Organización**: Estructura clara de archivos por plato
- **Optimización**: Formatos WebP para mejor rendimiento
- **Metadatos**: Información técnica completa por imagen

---

## 🎯 Beneficios del Sistema Multi-Imagen

### **📸 Para Contenido Visual Rico**
- Múltiples perspectivas del mismo plato
- Detalles de preparación y presentación
- Galería visual por elemento del menú
- Flexibilidad en cantidad de imágenes

### **🌍 Para Accesibilidad Internacional**
- Textos alternativos localizados
- Cumplimiento normativo WCAG
- SEO multiidioma optimizado
- Experiencia inclusiva

### **🍽️ Para Restaurantes Premium**
- Presentación profesional de platos
- Storytelling visual gastronómico
- Diferenciación por calidad visual
- Impacto emocional en clientes

### **⚡ Para Rendimiento**
- Carga progresiva de imágenes
- Formatos optimizados (WebP)
- Metadatos para lazy loading
- CDN-ready con URLs completas

### **🔧 Para Desarrolladores**
- Estructura predecible de datos
- Manejo consistente de arrays
- Validación automática de formatos
- Integración sencilla con componentes

Este sistema proporciona una base robusta para menús con contenido visual rico, manteniendo la simplicidad de uso mientras ofrece máxima flexibilidad para la presentación gastronómica profesional. 🚀📷
