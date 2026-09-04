# Guía Frontend: cuándo rellenar `common` vs `locales` al crear un menú

Esta guía resuelve una duda concreta: **¿qué propiedades van en `common` y cuáles en `locales` al crear o editar un menú?**

> **Respuesta corta:** `common` lleva todo lo que **NO es traducible** (precios, fechas, imágenes, IDs, alérgenos). `locales.{locale}.data` lleva solo lo **traducible** (nombres, títulos, descripciones). No es criterio del frontend: **lo decide el template**.

---

## 1. La regla la decide el template

Cada `field` del template tiene un flag `translatable`. Ese flag determina dónde se rellena el dato:

| `translatable` en el template | Dónde va el dato | Ejemplos típicos |
|---|---|---|
| `false` | **`common`** | `price`, `date`, `_id`, `image` (URL), `allergens` (array) |
| `true` | **`locales.{locale}.data`** | `name`, `title`, `description` |

Antes de rellenar un menú, mirá la definición del template (`GET /api/menu-templates/:id`) y revisá el `translatable` de cada campo. Ese es el mapa.

### Ejemplo de template

```jsonc
{
  "sections": [
    {
      "key": "header",
      "repeatable": false,
      "fields": [
        { "key": "title", "type": "text", "translatable": true  },  // → locale
        { "key": "date",  "type": "date", "translatable": false }   // → common
      ]
    },
    {
      "key": "items",
      "repeatable": true,
      "fields": [
        { "key": "_id",   "type": "text",  "translatable": false }, // → common (llave)
        { "key": "name",  "type": "text",  "translatable": true  }, // → locale
        { "key": "price", "type": "price", "translatable": false }  // → common
      ]
    }
  ]
}
```

---

## 2. Cómo se rellena al crear el menú

### Paso 1 — Crear el menú con `common` (lo no traducible)

`POST /api/menus`

```jsonc
{
  "tenant_id": "aralar",
  "name": "Menú diario 5 septiembre",
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

### Paso 2 — Agregar la traducción (lo traducible)

`PUT /api/menus/:id/locales/es-ES`

```jsonc
{
  "data": {
    "header": { "title": "Menú del día" },
    "items": [
      { "_id": "dish-gazpacho", "name": "Gazpacho" },
      { "_id": "dish-tortilla", "name": "Tortilla de patatas" }
    ]
  },
  "meta": {
    "title": "Menú del día",
    "summary": "Gazpacho y tortilla de patatas · 9,70 € I.V.A. incl."
  }
}
```

Se repite el `PUT .../locales/en-GB` para cada idioma adicional.

---

## 3. ⚠️ El error más común: el `_id` en secciones repetibles

En las **secciones repetibles** (arrays de platos), **cada item de `common` DEBE llevar su `_id`**, aunque el `_id` no sea un dato visible. Es la **llave de cruce** que usa el backend para unir el precio (de `common`) con el nombre (del `locale`).

```jsonc
// common  → el _id es OBLIGATORIO aquí
"items": [
  { "_id": "dish-gazpacho", "price": 5.5 },
  { "_id": "dish-tortilla", "price": 4.2 }
]

// locales.es-ES.data  → mismo _id + solo lo traducible
"items": [
  { "_id": "dish-gazpacho", "name": "Gazpacho" },
  { "_id": "dish-tortilla", "name": "Tortilla de patatas" }
]
```

**Si falta o no coincide el `_id`:** el precio NO se pega al plato y el item sale incompleto en el render. El `_id` debe ser idéntico en `common` y en cada `locale`.

---

## 4. Qué pasa en el render (`GET /menus/:id/render?locale=es-ES`)

El backend toma `common` como base y le superpone el bloque traducible del locale, dejando cada propiedad en su sitio:

- **Secciones no repetibles** (dict, ej. `header`): fusiona claves
  `common {date}` + `locale {title}` → `{ title, date }`
- **Secciones repetibles** (array, ej. `items`): fusiona **por `_id`**
  `{_id, price}` + `{_id, name}` → `{ _id, name, price }`

### Resultado final

```jsonc
{
  "data": {
    "header": {
      "title": "Menú del día",   // viene del locale
      "date": "2025-09-05"        // viene de common
    },
    "items": [
      { "_id": "dish-gazpacho", "name": "Gazpacho", "price": 5.5 },
      { "_id": "dish-tortilla", "name": "Tortilla de patatas", "price": 4.2 }
    ]
  }
}
```

---

## 5. Comportamientos del backend que debés conocer

Esto explica por qué a veces "lo que mando no aparece":

### a) `common` siempre gana sobre `locale`
Si por error ponés un precio (o cualquier campo no traducible) dentro del `locale`, el render **lo ignora**: para cualquier clave que exista en ambos lados, gana el valor de `common`.

### b) Al guardar `common`, el backend limpia los locales automáticamente
Cualquier clave que viva en `common` se **borra** del bloque equivalente de cada locale, porque se considera no-traducible. Es decir: si metés `name` en `common` "para probar", el sistema empezará a tratar `name` como no-traducible y lo quitará de las traducciones existentes.

**Conclusión:** no mezcles. Cada campo va en un solo lado, según su `translatable`.

---

## 6. Checklist rápido para el frontend

- [ ] Leer el template y anotar qué campos son `translatable: true` y cuáles `false`.
- [ ] Campos `translatable: false` → al objeto `common`.
- [ ] Campos `translatable: true` → a `locales.{locale}.data`.
- [ ] En secciones repetibles, incluir el **`_id` en `common` Y en cada `locale`**, idéntico.
- [ ] No duplicar un mismo campo en ambos lados (se limpia / se ignora).
- [ ] `meta.title` y `meta.summary` van en cada `locale` (son traducibles, para listados públicos).

---

## 7. Referencia visual

```
TEMPLATE (estructura + flag translatable)
   │
   ├── translatable: false ──────────────► MENÚ.common
   │      price, date, _id, image, allergens
   │
   └── translatable: true ───────────────► MENÚ.locales.{locale}.data
          name, title, description

                         │
                         ▼
        GET /render?locale=es-ES  →  fusiona common + locale
                         │
                         ▼
              data: { secciones con todos los campos juntos }
```
