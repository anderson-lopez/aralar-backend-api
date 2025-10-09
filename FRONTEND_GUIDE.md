# Guía Frontend — Menús Dinámicos de Aralar

Documento para desarrolladores Frontend que construirán UI de templates y menús, y consumirán los endpoints de la API. Cubre conceptos, contratos de datos, mapeos a componentes, flujos, i18n, medios, catálogos, disponibilidad, accesibilidad y testing.

## 📋 Tabla de Contenidos

1. [Conceptos clave](#conceptos-clave)
2. [Contratos de datos](#contratos-de-datos)
3. [Flujo recomendado](#flujo-recomendado)
4. [Mapeo UI → Componentes](#mapeo-ui--componentes)
5. [Disponibilidad](#disponibilidad)
6. [Imágenes](#imágenes)
7. [Internacionalización (i18n)](#internacionalización-i18n)
8. [Autenticación](#autenticación)
9. [Endpoints principales](#endpoints-principales)

## 1. Conceptos clave

### Multi-tenancy
Aralar API es **multi-tenant**: una sola API sirve múltiples restaurantes/clientes. Cada entidad (templates, menús, usuarios) pertenece a un `tenant_id` específico:

- **"aralar"**: Restaurante principal
- **"casa-pepe"**: Cliente Casa Pepe  
- **"la-taberna"**: Cliente La Taberna

**Como frontend:** Los datos vienen automáticamente filtrados por tenant. No necesitas manejar manualmente el `tenant_id` en requests públicos.

### Template
Define la estructura y semántica de una carta (secciones, campos, UI). Se reutiliza para crear muchos menús.

### Menú
Una instancia de contenido que usa un template. Tiene:
- **common**: estructura no traducible (ids técnicos, medios, precios, alérgenos…)
- **locales[lang].data**: contenido traducible (títulos, nombres, descripciones…)
- **locales[lang].meta**: metadatos traducibles para listados (título, resumen)
- **availability**: días/fechas en los que está disponible

### Render
Endpoint que entrega el menú listo para pintar, con datos fusionados por locale y un UI manifest (`include_ui=true`) que describe cómo renderizar secciones.

## 2. Contratos de datos

### 2.1 Template (creación/edición)

```json
{
  "name": "Menú diario básico",
  "slug": "daily-basic-ui",
  "tenant_id": "aralar",
  "version": 1,
  "status": "draft",
  "i18n": { 
    "default_locale": "es-ES", 
    "locales": ["es-ES","en-GB"] 
  },
  "sections": [
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
        },
        { 
          "key": "description", 
          "type": "textarea", 
          "translatable": true 
        },
        { 
          "key": "allergens", 
          "type": "tags", 
          "enum": ["fish","eggs","milk","gluten"] 
        },
        {
          "key": "images", 
          "type": "list", 
          "translatable": false,
          "itemSchema": { 
            "fields": [
              { "key":"url","type":"text","required":true },
              { "key":"mime","type":"text","required":true },
              { "key":"width","type":"number" }, 
              { "key":"height","type":"number" }, 
              { "key":"size","type":"number" }
            ]
          }
        },
        { 
          "key": "images_alt", 
          "type": "list", 
          "translatable": true 
        }
      ],
      "ui": {
        "role": "course_list",
        "order": 10,
        "display": "list",
        "hints": { 
          "show_price": false, 
          "supports_multi_images": true 
        }
      }
    }
  ],
  "ui": {
    "layout": "sections",
    "catalogs": {
      "allergens": [ 
        { "code":"fish","icon":"afish" }, 
        { "code":"eggs","icon":"aegg" } 
      ],
      "currency": { 
        "code":"EUR",
        "symbol":"€",
        "locale":"es-ES" 
      }
    }
  }
}
```

#### Tipos válidos de fields

**Tipos básicos:**
- `text` | `textarea` | `rich_text` | `number` | `price` | `boolean`
- `date` | `time` | `datetime` | `enum` | `multi_enum` | `tags`
- `image` | `list` | `group` | `reference` | `divider` | `subtitle`

#### Semántica UI

**Roles disponibles:**
- `header` | `course_list` | `extras` | `legend` | `note` | `price_footer`

**Display modes:**
- `hero` | `list` | `bullets` | `table` | `grid` | `legend` | `footer_price`

**Hints comunes:**
- `choose_count?: number`
- `scope?: "per_table" | "per_person"`
- `show_price?: boolean`
- `icon?: string`
- `supports_multi_images?: boolean`

> **Regla:** Definir siempre `label` al menos en `i18n.default_locale`. Otros idiomas son opcionales y se añaden más tarde (manualmente o vía endpoint de traducción).

### 2.2 Menú (creación/edición)

```json
{
  "tenant_id": "aralar",
  "template_slug": "daily-basic-ui",
  "template_version": 1,
  "status": "draft",
  "common": {
    "starters": [
      {
        "_id": "soup",
        "allergens": ["milk"],
        "images": [{ 
          "url":"https://cdn/uuid.webp", 
          "mime":"image/webp", 
          "width":1200, 
          "height":900 
        }]
      }
    ],
    "footer": { 
      "price_total": 12.9, 
      "vat_percent": 10, 
      "vat_included": true 
    }
  }
}
```

**Locales (traducible) + meta:**

```json
{
  "data": {
    "starters": [
      { 
        "_id":"soup", 
        "name":"Sopa del día", 
        "images_alt":["Sopa de verduras"] 
      }
    ],
    "header": { 
      "title":"Menú del día", 
      "subtitle":"Incluye bebida" 
    },
    "footer": { 
      "note": "I.V.A. incluido" 
    }
  },
  "meta": { 
    "title":"Menú del día", 
    "summary":"Entrante y principal · 12,90 € I.V.A. incl." 
  }
}
```

> **Anclaje por _id:** cada item repetible usa `_id` en common, y el mismo `_id` para su traducción en `locales[lang].data`.

### 2.3 Render (consumo público/privado)

```http
GET /api/menus/:id/render?locale=es-ES&include_ui=true
```

```json
{
  "id":"...", 
  "tenant_id":"aralar",
  "template":{"slug":"daily-basic-ui","version":1},
  "locale":"es-ES",
  "meta": { 
    "title":"Menú del día", 
    "summary":"..." 
  },
  "ui": {
    "layout":"sections",
    "sections":[
      { 
        "key":"starters",
        "role":"course_list",
        "order":10,
        "display":"list",
        "labels":{"es-ES":"Entrantes","en-GB":"Starters"},
        "hints":{"show_price":false,"supports_multi_images":true} 
      },
      { 
        "key":"footer",
        "role":"price_footer",
        "order":90,
        "display":"footer_price",
        "labels":{"es-ES":"Precio"} 
      }
    ],
    "catalogs": {
      "allergens":[ 
        {"code":"fish","icon":"afish"}, 
        {"code":"eggs","icon":"aegg"} 
      ],
      "currency":{"code":"EUR","symbol":"€","locale":"es-ES"}
    }
  },
  "data": {
    "starters":[
      { 
        "_id":"soup",
        "name":"Sopa del día",
        "allergens":["milk"],
        "images":[{
          "url":"https://cdn/uuid.webp",
          "mime":"image/webp",
          "width":1200,
          "height":900
        }],
        "images_alt":["Sopa de verduras"] 
      }
    ],
    "footer": { 
      "price_total":12.9, 
      "vat_percent":10, 
      "vat_included":true, 
      "note":"I.V.A. incluido" 
    }
  }
}
```

> **Compatibilidad:** si el template viejo usa `image`/`image_alt`, el backend de `/render` normaliza a `images[]` y `images_alt[]`.

## 3. Flujo recomendado

### 3.1 Crear/editar Template
1. Definir `sections[]` con `fields[]`, `ui.role`/`order`/`display`/`hints`
2. Poner `label` al menos en `i18n.default_locale`
3. Publicar el template
4. (Opcional) añadir idiomas a labels (PATCH o auto-traducción con `/api/i18n/translate`)

### 3.2 Crear/editar Menú
1. Crear menú con `common` (estructura, medios, alérgenos, precios)
2. Cargar `locales[lang].data` (textos) y `locales[lang].meta` (title/summary)
3. Establecer `availability` (timezone, days_of_week, date_ranges)
4. Publicar locales necesarios

### 3.3 Consumir Público
1. **Listado:** `GET /api/menus/public/available?locale=es-ES&tz=Europe/Madrid[&fallback=en-GB]`
   - Devuelve tarjetas: id, title, summary, template_slug/version
2. **Detalle:** `GET /api/menus/:id/render?locale=es-ES&include_ui=true`
   - Renderizar secciones por `ui.sections` (orden ascendente)
   - Mapear `role`/`display` → componentes
   - Usar `ui.catalogs` para iconos de alérgenos y currency para precios

## 4. Mapeo UI → Componentes

### Tipos TypeScript sugeridos

```typescript
type Role = "header" | "course_list" | "extras" | "legend" | "note" | "price_footer";
type Display = "hero" | "list" | "bullets" | "table" | "grid" | "legend" | "footer_price";

const ROLE_TO_COMPONENT: Record<Role, React.FC<any>> = {
  header: HeaderHero,
  course_list: CourseList,
  extras: BulletList,
  legend: Legend,
  note: NoteBlock,
  price_footer: PriceFooter
};
```

### Componente principal de renderizado

```tsx
function MenuRender({ payload }: { payload: RenderPayload }) {
  const sections = (payload.ui?.sections ?? [])
    .slice()
    .sort((a,b) => a.order - b.order);
    
  return (
    <div className="menu">
      {sections.map(sec => {
        const Comp = ROLE_TO_COMPONENT[sec.role as Role];
        if (!Comp) return null;
        
        const sectionData = payload.data[sec.key];
        const labelResolved =
          sec.labels?.[payload.locale] ??
          sec.labels?.[payload.templateDefaultLocale] ??
          sec.key;
          
        return (
          <section key={sec.key} data-role={sec.role}>
            <Comp
              keyName={sec.key}
              display={sec.display}
              label={labelResolved}
              data={sectionData}
              hints={sec.hints}
              catalogs={payload.ui?.catalogs}
              locale={payload.locale}
            />
          </section>
        );
      })}
    </div>
  );
}
```

### Componente CourseList (ejemplo completo)

```tsx
function CourseList({ 
  label, 
  data, 
  hints, 
  catalogs 
}: {
  label: string; 
  data: any[]; 
  hints?: any; 
  catalogs?: any;
}) {
  const allergenMap = new Map<string, any>();
  catalogs?.allergens?.forEach((a: any) => 
    allergenMap.set(a.code, a)
  );
  
  return (
    <div className={`course-list display-${hints?.display || "list"}`}>
      <h3 className="section-title">
        {label}
        {hints?.choose_count && (
          <small>
            · A elegir {hints.choose_count}
            {hints.scope === "per_table" ? " por mesa" : 
             hints.scope === "per_person" ? " por persona" : ""}
          </small>
        )}
      </h3>
      
      <ul className="items">
        {(data || []).map((item: any) => {
          const images = Array.isArray(item.images) 
            ? item.images 
            : (item.image ? [item.image] : []);
          const alts = Array.isArray(item.images_alt) 
            ? item.images_alt 
            : (item.image_alt ? [item.image_alt] : []);
            
          return (
            <li key={item._id} className="item">
              <div className="name">{item.name}</div>
              
              {images.length > 0 && (
                <div className={`gallery ${
                  hints?.supports_multi_images ? "carousel" : "single"
                }`}>
                  {images.map((media: any, idx: number) => (
                    <img 
                      key={media.url} 
                      src={media.url} 
                      alt={alts[idx] || item.name || ""}
                      width={media.width}
                      height={media.height}
                    />
                  ))}
                </div>
              )}
              
              {Array.isArray(item.allergens) && item.allergens.length > 0 && (
                <div className="allergens">
                  {item.allergens.map((code: string) => {
                    const allergen = allergenMap.get(code);
                    return (
                      <i 
                        key={code} 
                        className={`allergen ${allergen?.icon || code}`} 
                        title={allergen?.labels?.["es-ES"] || code} 
                      />
                    );
                  })}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
```

## 5. Disponibilidad

- En el listado público, la API ya filtra por `tz`, `days_of_week` y `date_ranges`
- Puedes mostrar un "badge" con días disponibles si el endpoint te lo devuelve (opcional)
- Para vistas futuras, confirma con el backend si planean ampliar con horarios

## 6. Imágenes

### Mejores prácticas

- **Consumo:** usar URLs absolutas (CDN/S3/MinIO detrás de CDN)
- **Performance:** Placeholder + lazy loading (optimizar LCP)
- **ALT:** tomar de `images_alt[idx]` (si no existe, fallback a `name` del plato)
- **Compatibilidad:** si llega `image`/`image_alt` singular, el backend normaliza a arrays en `/render`

### Ejemplo de implementación

```tsx
function LazyImage({ 
  src, 
  alt, 
  width, 
  height 
}: {
  src: string;
  alt: string;
  width?: number;
  height?: number;
}) {
  return (
    <img 
      src={src}
      alt={alt}
      width={width}
      height={height}
      loading="lazy"
      style={{ aspectRatio: width && height ? `${width}/${height}` : 'auto' }}
    />
  );
}
```

## 7. Internacionalización (i18n)

### Reglas Frontend

1. **Pedir siempre locale** en:
   - `/public/available?locale=xx-YY`
   - `/menus/:id/render?locale=xx-YY&include_ui=true`

2. **Fallback recomendado:** si no hay traducción visible de label, mostrar `default_locale` o `key`

3. **Labels de secciones** vienen en `ui.sections[*].labels`

4. **Contenido** viene en `data` ya mergeado por locale

5. **Título/Resumen** para listados: la API entrega `meta.title`/`meta.summary` resueltos en `/public/available`

### Idiomas soportados

La API soporta 100+ idiomas incluyendo:
- **Europeos:** es, en, fr, de, it, pt, eu (euskera), ca (catalán), gl (gallego)
- **Asiáticos:** zh, ja, ko, th, vi, hi
- **Otros:** ar, he, fa, ru

## 8. Autenticación

### Para endpoints privados

```typescript
// Configurar JWT token
const token = localStorage.getItem('jwt_token');

const apiClient = {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
};

// El token se mantiene en Swagger UI entre recargas
```

### Manejo de errores de token

```typescript
async function apiCall(url: string, options: RequestInit = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      ...options.headers
    }
  });
  
  if (response.status === 401) {
    // Token expirado o invalidado
    redirectToLogin();
    return;
  }
  
  return response.json();
}
```

## 9. Endpoints principales

### Públicos (sin autenticación)

```http
# Listado de menús disponibles
GET /api/menus/public/available?locale=es-ES&tz=Europe/Madrid

# Menús destacados para landing
GET /api/menus/public/featured?locale=es-ES&tz=Europe/Madrid&include_ui=true

# Renderizado de menú específico
GET /api/menus/{id}/render?locale=es-ES&include_ui=true

# Catálogo de alérgenos
GET /api/catalogs/allergens
```

### Privados (requieren autenticación)

```http
# Gestión de templates
GET /api/menu-templates
POST /api/menu-templates
PUT /api/menu-templates/{slug}/versions/{version}

# Gestión de menús
GET /api/menus
POST /api/menus
PUT /api/menus/{id}
PUT /api/menus/{id}/featured

# Traducciones
POST /api/i18n/translate
GET /api/i18n/cache

# Subida de archivos
POST /api/uploads/presign
POST /api/uploads/proxy-put
```

### Respuestas de error estándar

```json
{
  "error": "ValidationError",
  "message": "Invalid field value",
  "details": {
    "field": "locale", 
    "code": "invalid_choice"
  }
}
```

---

## 📚 Recursos adicionales

- **Swagger UI:** `/api/docs` (documentación interactiva)
- **Redoc:** `/api/redoc` (documentación estática)
- **Health check:** `/api/health`

## 🔧 Configuración recomendada

```typescript
// config/api.ts
export const API_CONFIG = {
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  defaultLocale: 'es-ES',
  defaultTimezone: 'Europe/Madrid',
  fallbackLocale: 'en-GB'
};
```

---

*Documentación actualizada para Aralar API v1.0*
