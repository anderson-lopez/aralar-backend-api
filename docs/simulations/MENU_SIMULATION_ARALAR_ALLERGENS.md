# Simulación Menú Aralar con Alérgenos

Este documento simula la creación completa de un menú tipo "Menú Aralar" con iconos de alérgenos, siguiendo el nuevo formato con secciones personalizadas y UI manifest.

## Objetivo del Menú

- **Sección Cabecera**: Título "Menú Aralar"
- **Sección Entrantes**: "Dos entrantes a elegir por mesa", lista de platos con iconos de alérgenos (sin precio)
- **Sección Platos principales**: "A elegir" (1 por persona), lista de platos con iconos (sin precio)
- **Sección Extras**: Tipo bullets ("Postre…", "Vino…", "Agua y Pan")
- **Pie de precio**: "38,00 € · 10% I.V.A. incluido"

---

## 1. Crear TEMPLATE (draft)

```http
POST /api/menu-templates
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "name": "Menú Aralar con alérgenos",
  "slug": "aralar-allergen-menu",
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
        "es-ES": "Dos entrantes a elegir por mesa", 
        "en-GB": "Two starters per table" 
      },
      "repeatable": true,
      "minItems": 1,
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
          "enum": [
            "gluten", "crustaceans", "eggs", "fish", "peanuts", "soy", 
            "milk", "nuts", "celery", "mustard", "sesame", "sulfites", 
            "lupin", "molluscs"
          ]
        }
      ],
      "ui": {
        "role": "course_list", 
        "order": 10, 
        "display": "list",
        "hints": { 
          "choose_count": 2, 
          "scope": "per_table", 
          "show_price": false, 
          "icon": "utensils" 
        }
      }
    },
    {
      "key": "mains",
      "label": { 
        "es-ES": "A elegir", 
        "en-GB": "Main course" 
      },
      "repeatable": true,
      "minItems": 1,
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
          "enum": [
            "gluten", "crustaceans", "eggs", "fish", "peanuts", "soy", 
            "milk", "nuts", "celery", "mustard", "sesame", "sulfites", 
            "lupin", "molluscs"
          ]
        }
      ],
      "ui": {
        "role": "course_list", 
        "order": 20, 
        "display": "list",
        "hints": { 
          "choose_count": 1, 
          "scope": "per_person", 
          "show_price": false, 
          "icon": "utensils" 
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
          "required": true, 
          "translatable": false, 
          "currency": "EUR" 
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
        },
        { 
          "key": "note", 
          "type": "text", 
          "required": false, 
          "translatable": true 
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
      ]
    }
  }
}
```

**Respuesta esperada:**
```json
{
  "id": "6720a1000000000000000001"
}
```

---

## 2. Publicar TEMPLATE

```http
POST /api/menu-templates/6720a1000000000000000001/publish
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "notes": "v1 publicada - Menú Aralar con alérgenos"
}
```

**Respuesta esperada:**
```json
{
  "id": "6720a1000000000000000002"
}
```

---

## 3. Crear MENÚ (draft)

```http
POST /api/menus
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "tenant_id": "aralar",
  "name": "Menú Aralar alérgenos",
  "template_slug": "aralar-allergen-menu",
  "template_version": 1,
  "status": "draft",
  "common": {
    "footer": { 
      "price_total": 38.0, 
      "vat_percent": 10, 
      "vat_included": true 
    },
    "extras": [
      { "_id": "dessert", "text": "Postre a elegir del menú" },
      { "_id": "wine", "text": "Vino Crianza (1/2 por persona)" },
      { "_id": "water", "text": "Agua y Pan" }
    ],
    "starters": [
      { "_id": "ens-mixta", "allergens": ["milk"] },
      { "_id": "ens-rusa", "allergens": ["eggs", "milk"] },
      { "_id": "esparragos", "allergens": ["milk"] },
      { "_id": "ventresca-piperrada", "allergens": ["fish"] },
      { "_id": "queso-cabra-pasas", "allergens": ["milk", "nuts"] },
      { "_id": "cecina-parmesano-romero", "allergens": ["milk"] },
      { "_id": "ibericos", "allergens": [] },
      { "_id": "rev-bacalao", "allergens": ["eggs", "fish"] },
      { "_id": "rev-hongos", "allergens": ["eggs"] },
      { "_id": "salmon-encurtidos", "allergens": ["fish", "milk"] },
      { "_id": "rabas", "allergens": ["gluten"] },
      { "_id": "croquetas", "allergens": ["gluten", "eggs", "milk", "nuts", "celery"] }
    ],
    "mains": [
      { "_id": "merluza-plancha-salsa-verde", "allergens": ["fish", "gluten", "milk", "soy"] },
      { "_id": "bacalao-pilpil-bizkaina", "allergens": ["fish", "milk"] },
      { "_id": "confit-pato-frutos-rojos", "allergens": ["milk", "nuts"] },
      { "_id": "rabo-ternera-rioja", "allergens": ["milk", "sulfites"] },
      { "_id": "entrecot-patatas-piquillos", "allergens": [] }
    ]
  }
}
```

**Respuesta esperada:**
```json
{
  "_id": "6720a1000000000000000003",
  "name": "Menú Aralar alérgenos"
}
```

---

## 4. Configurar Disponibilidad

```http
PUT /api/menus/6720a1000000000000000003/availability
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

---

## 5. Localización Español (es-ES)

```http
PUT /api/menus/6720a1000000000000000003/locales/es-ES
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "data": {
    "header": { 
      "title": "Menú Aralar" 
    },
    "starters": [
      { "_id": "ens-mixta", "name": "Ensalada Mixta" },
      { "_id": "ens-rusa", "name": "Ensaladilla Rusa" },
      { "_id": "esparragos", "name": "Espárragos" },
      { "_id": "ventresca-piperrada", "name": "Ensalada de ventresca con piperrada" },
      { "_id": "queso-cabra-pasas", "name": "Ensalada de queso de cabra y pasas" },
      { "_id": "cecina-parmesano-romero", "name": "Cecina con lascas de parmesano y aceite de romero" },
      { "_id": "ibericos", "name": "Surtido de Ibéricos" },
      { "_id": "rev-bacalao", "name": "Revuelto de bacalao" },
      { "_id": "rev-hongos", "name": "Revuelto de hongos" },
      { "_id": "salmon-encurtidos", "name": "Salmón ahumado con vinagreta de encurtidos" },
      { "_id": "rabas", "name": "Rabas" },
      { "_id": "croquetas", "name": "Croquetas" }
    ],
    "mains": [
      { "_id": "merluza-plancha-salsa-verde", "name": "Merluza frita, plancha o salsa verde" },
      { "_id": "bacalao-pilpil-bizkaina", "name": "Bacalao pil-pil ó bizkaina" },
      { "_id": "confit-pato-frutos-rojos", "name": "Confit de pato con salsa de frutos rojos" },
      { "_id": "rabo-ternera-rioja", "name": "Rabo de ternera guisado al Rioja Alavesa" },
      { "_id": "entrecot-patatas-piquillos", "name": "Entrecot plancha con patatas fritas y piquillos" }
    ],
    "footer": { 
      "note": "I.V.A. incluido" 
    }
  }
}
```

---

## 6. Publicar Localización Español

```http
POST /api/menus/6720a1000000000000000003/publish/es-ES
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "notes": "Menú Aralar ES publicado"
}
```

**Respuesta esperada:**
```json
{
  "message": "ok"
}
```

---

## 7. Localización Inglés (en-GB) - Opcional

```http
PUT /api/menus/6720a1000000000000000003/locales/en-GB
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "data": {
    "header": { 
      "title": "Aralar Menu" 
    },
    "starters": [
      { "_id": "ens-mixta", "name": "Mixed Salad" },
      { "_id": "ens-rusa", "name": "Russian Salad" },
      { "_id": "esparragos", "name": "Asparagus" },
      { "_id": "ventresca-piperrada", "name": "Tuna belly salad with peppers" },
      { "_id": "queso-cabra-pasas", "name": "Goat cheese and raisins salad" },
      { "_id": "cecina-parmesano-romero", "name": "Cured beef with parmesan and rosemary oil" },
      { "_id": "ibericos", "name": "Iberian Ham Selection" },
      { "_id": "rev-bacalao", "name": "Scrambled eggs with cod" },
      { "_id": "rev-hongos", "name": "Scrambled eggs with mushrooms" },
      { "_id": "salmon-encurtidos", "name": "Smoked salmon with pickled vegetables vinaigrette" },
      { "_id": "rabas", "name": "Fried Squid Rings" },
      { "_id": "croquetas", "name": "Croquettes" }
    ],
    "mains": [
      { "_id": "merluza-plancha-salsa-verde", "name": "Hake fried, grilled or green sauce" },
      { "_id": "bacalao-pilpil-bizkaina", "name": "Cod pil-pil or Biscayan style" },
      { "_id": "confit-pato-frutos-rojos", "name": "Duck confit with red berry sauce" },
      { "_id": "rabo-ternera-rioja", "name": "Beef tail stewed in Rioja Alavesa wine" },
      { "_id": "entrecot-patatas-piquillos", "name": "Grilled entrecote with fries and peppers" }
    ],
    "footer": { 
      "note": "V.A.T. included" 
    }
  }
}
```

---

## 8. Render Final con UI Manifest (Público)

```http
GET /api/menus/6720a1000000000000000003/render?locale=es-ES&with_ui=1
```

**Respuesta esperada (resumen):**
```json
{
  "id": "6720a1000000000000000003",
  "name": "Menú Aralar alérgenos",
  "template": { 
    "slug": "aralar-allergen-menu", 
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
        "hints": {
          "choose_count": 2,
          "scope": "per_table",
          "show_price": false,
          "icon": "utensils"
        },
        "labels": { "es-ES": "Dos entrantes a elegir por mesa" }
      },
      { 
        "key": "mains",
        "role": "course_list",
        "order": 20,
        "display": "list",
        "hints": {
          "choose_count": 1,
          "scope": "per_person",
          "show_price": false,
          "icon": "utensils"
        },
        "labels": { "es-ES": "A elegir" }
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
      "allergens": [
        { "code": "gluten", "icon": "agluten", "labels": { "es-ES": "Gluten", "en-GB": "Gluten" }},
        { "code": "crustaceans", "icon": "acrusta", "labels": { "es-ES": "Crustáceos", "en-GB": "Crustaceans" }},
        { "code": "eggs", "icon": "aegg", "labels": { "es-ES": "Huevos", "en-GB": "Eggs" }},
        { "code": "fish", "icon": "afish", "labels": { "es-ES": "Pescado", "en-GB": "Fish" }},
        { "code": "peanuts", "icon": "apeanut", "labels": { "es-ES": "Cacahuetes", "en-GB": "Peanuts" }},
        { "code": "soy", "icon": "asoy", "labels": { "es-ES": "Soja", "en-GB": "Soy" }},
        { "code": "milk", "icon": "amilk", "labels": { "es-ES": "Leche/Lactosa", "en-GB": "Milk" }},
        { "code": "nuts", "icon": "anuts", "labels": { "es-ES": "Frutos secos", "en-GB": "Tree nuts" }},
        { "code": "celery", "icon": "acelery", "labels": { "es-ES": "Apio", "en-GB": "Celery" }},
        { "code": "mustard", "icon": "amustard", "labels": { "es-ES": "Mostaza", "en-GB": "Mustard" }},
        { "code": "sesame", "icon": "asesame", "labels": { "es-ES": "Sésamo", "en-GB": "Sesame" }},
        { "code": "sulfites", "icon": "asulfite", "labels": { "es-ES": "Sulfitos", "en-GB": "Sulphites" }},
        { "code": "lupin", "icon": "alupin", "labels": { "es-ES": "Altramuces", "en-GB": "Lupin" }},
        { "code": "molluscs", "icon": "amollusc", "labels": { "es-ES": "Moluscos", "en-GB": "Molluscs" }}
      ],
      "currency": { 
        "code": "EUR", 
        "symbol": "€", 
        "locale": "es-ES" 
      }
    }
  },
  "data": {
    "header": { 
      "title": "Menú Aralar" 
    },
    "starters": [
      { "_id": "ens-mixta", "name": "Ensalada Mixta", "allergens": ["milk"] },
      { "_id": "ens-rusa", "name": "Ensaladilla Rusa", "allergens": ["eggs", "milk"] },
      { "_id": "esparragos", "name": "Espárragos", "allergens": ["milk"] },
      { "_id": "ventresca-piperrada", "name": "Ensalada de ventresca con piperrada", "allergens": ["fish"] },
      { "_id": "queso-cabra-pasas", "name": "Ensalada de queso de cabra y pasas", "allergens": ["milk", "nuts"] },
      { "_id": "cecina-parmesano-romero", "name": "Cecina con lascas de parmesano y aceite de romero", "allergens": ["milk"] },
      { "_id": "ibericos", "name": "Surtido de Ibéricos", "allergens": [] },
      { "_id": "rev-bacalao", "name": "Revuelto de bacalao", "allergens": ["eggs", "fish"] },
      { "_id": "rev-hongos", "name": "Revuelto de hongos", "allergens": ["eggs"] },
      { "_id": "salmon-encurtidos", "name": "Salmón ahumado con vinagreta de encurtidos", "allergens": ["fish", "milk"] },
      { "_id": "rabas", "name": "Rabas", "allergens": ["gluten"] },
      { "_id": "croquetas", "name": "Croquetas", "allergens": ["gluten", "eggs", "milk", "nuts", "celery"] }
    ],
    "mains": [
      { "_id": "merluza-plancha-salsa-verde", "name": "Merluza frita, plancha o salsa verde", "allergens": ["fish", "gluten", "milk", "soy"] },
      { "_id": "bacalao-pilpil-bizkaina", "name": "Bacalao pil-pil ó bizkaina", "allergens": ["fish", "milk"] },
      { "_id": "confit-pato-frutos-rojos", "name": "Confit de pato con salsa de frutos rojos", "allergens": ["milk", "nuts"] },
      { "_id": "rabo-ternera-rioja", "name": "Rabo de ternera guisado al Rioja Alavesa", "allergens": ["milk", "sulfites"] },
      { "_id": "entrecot-patatas-piquillos", "name": "Entrecot plancha con patatas fritas y piquillos", "allergens": [] }
    ],
    "extras": [
      { "_id": "dessert", "text": "Postre a elegir del menú" },
      { "_id": "wine", "text": "Vino Crianza (1/2 por persona)" },
      { "_id": "water", "text": "Agua y Pan" }
    ],
    "footer": { 
      "price_total": 38.0, 
      "vat_percent": 10, 
      "vat_included": true, 
      "note": "I.V.A. incluido" 
    }
  }
}
```

---

## 9. Endpoint de Catálogo de Alérgenos (Público)

Para obtener la lista completa de alérgenos disponibles:

```http
GET /api/catalogs/allergens?locale=es-ES
```

**Respuesta:**
```json
{
  "items": [
    { "code": "gluten", "icon": "agluten", "label": "Gluten" },
    { "code": "crustaceans", "icon": "acrusta", "label": "Crustáceos" },
    { "code": "eggs", "icon": "aegg", "label": "Huevos" },
    { "code": "fish", "icon": "afish", "label": "Pescado" },
    { "code": "peanuts", "icon": "apeanut", "label": "Cacahuetes" },
    { "code": "soy", "icon": "asoy", "label": "Soja" },
    { "code": "milk", "icon": "amilk", "label": "Leche/Lactosa" },
    { "code": "nuts", "icon": "anuts", "label": "Frutos secos" },
    { "code": "celery", "icon": "acelery", "label": "Apio" },
    { "code": "mustard", "icon": "amustard", "label": "Mostaza" },
    { "code": "sesame", "icon": "asesame", "label": "Sésamo" },
    { "code": "sulfites", "icon": "asulfite", "label": "Sulfitos" },
    { "code": "lupin", "icon": "alupin", "label": "Altramuces" },
    { "code": "molluscs", "icon": "amollusc", "label": "Moluscos" }
  ]
}
```

---

## Características del Menú Aralar

### ✨ **Funcionalidades Implementadas**

- **UI Manifest**: Información completa de layout y secciones
- **Alérgenos**: Catálogo completo con iconos y etiquetas multiidioma
- **Secciones Personalizadas**: Header, entrantes, principales, extras, footer
- **Hints de UI**: Indicaciones de selección (2 entrantes por mesa, 1 principal por persona)
- **Multiidioma**: Soporte para español e inglés
- **Precios**: Footer con precio total e IVA incluido

### 🎯 **Casos de Uso**

1. **Frontend puede renderizar** el menú usando el UI manifest
2. **Iconos de alérgenos** se muestran junto a cada plato
3. **Reglas de selección** claras (2 entrantes por mesa, 1 principal por persona)
4. **Información de precio** centralizada en el footer
5. **Catálogo público** de alérgenos disponible para referencia

### 📱 **Integración Frontend**

El frontend puede usar:
- `ui.sections` para el layout y orden de secciones
- `ui.catalogs.allergens` para mapear códigos a iconos y etiquetas
- `hints` para mostrar reglas de selección
- `data` para el contenido real del menú

Este formato permite una renderización flexible y consistente del menú Aralar con toda la información necesaria para mostrar alérgenos y reglas de selección.
