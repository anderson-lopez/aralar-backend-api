# Guía de Renderizado de Menús para Frontend

Esta guía explica cómo el frontend debe interpretar y renderizar los menús usando el contrato de la API de Aralar.

## 🔑 Guía Rápida de Naming para Fields.key

### Convención General
- **Formato**: `snake_case`, descriptivo y estable en el tiempo
- **Propósito**: Facilitar el mapeo automático entre backend y frontend
- **Consistencia**: Mismos nombres para funcionalidades similares

### Claves Típicas por Tipo de Sección

#### **Header (Cabecera)**
```typescript
{
  title: string,           // text, translatable - Título principal
  subtitle?: string,       // text, translatable - Subtítulo opcional
  banner_image?: ImageData, // image, no translatable - Imagen hero/banner
  banner_image_alt?: string // text, translatable - Alt text del banner
}
```

#### **Course/Platos (Items Repetibles)**
```typescript
{
  _id: string,            // text, no trans - Ancla técnica para locales
  name: string,           // text, trans - Nombre del plato
  description?: string,   // textarea/rich_text, trans - Descripción opcional
  price?: number,         // price, no trans - Precio (si el diseño lo requiere)
  image?: ImageData,      // image, no trans - Foto del plato
  image_alt?: string,     // text, trans - Alt text de la imagen
  allergens?: string[],   // tags, no trans - Códigos del catálogo de alérgenos
  badges?: string[]       // tags/enum, no trans - spicy, vegan, gluten_free, etc.
}
```

#### **Extras (Bullets/Incluidos)**
```typescript
{
  _id: string,           // text, no trans - Identificador técnico
  text: string           // text, trans - Texto descriptivo
}
```

#### **Footer (Pie de Precio)**
```typescript
{
  price_total: number,    // price, no trans - Precio total
  vat_percent?: number,   // number, no trans - Porcentaje de IVA
  vat_included?: boolean, // boolean, no trans - IVA incluido/no incluido
  note?: string          // text, trans - Nota adicional
}
```

### Diferenciación Semántica de Imágenes

#### **¿Por qué `banner_image` vs `image`?**

- **`banner_image`** en header → Denota contexto de "hero/header" (1:1, imagen principal)
- **`image`** en items → Genérico por elemento (múltiples, galería de platos)

Esta diferenciación ayuda al frontend a:
- **Decidir layout automáticamente** sin depender del nombre de la sección
- **Aplicar estilos específicos** (hero vs thumbnail)
- **Optimizar carga** (banner prioritario, platos lazy-load)

### Ejemplos Prácticos

#### **Menú Simple**
```json
{
  "header": {
    "title": "Menú del día",
    "subtitle": "Incluye bebida"
  },
  "items": [
    {
      "_id": "gazpacho",
      "name": "Gazpacho",
      "price": 5.50
    }
  ],
  "footer": {
    "price_total": 12.90,
    "vat_included": true
  }
}
```

#### **Menú con Imágenes**
```json
{
  "header": {
    "title": "Menú Aralar",
    "banner_image": {
      "url": "https://cdn.example.com/banner.webp",
      "width": 1600,
      "height": 600
    },
    "banner_image_alt": "Vista del restaurante Aralar"
  },
  "starters": [
    {
      "_id": "ensalada",
      "name": "Ensalada mixta",
      "image": {
        "url": "https://cdn.example.com/ensalada.webp",
        "width": 400,
        "height": 300
      },
      "image_alt": "Ensalada fresca con ingredientes de temporada",
      "allergens": ["milk", "nuts"]
    }
  ]
}
```

#### **Menú con Badges y Alérgenos**
```json
{
  "mains": [
    {
      "_id": "pasta-vegan",
      "name": "Pasta con verduras",
      "description": "Pasta integral con verduras de temporada",
      "price": 14.50,
      "badges": ["vegan", "organic"],
      "allergens": ["gluten"]
    }
  ]
}
```

### Beneficios de Esta Convención

#### **🔧 Para el Frontend**
- **Mapeo automático**: `data[section.key][field.key]` siempre funciona
- **Componentes reutilizables**: Misma estructura, diferentes contenidos
- **Tipado fuerte**: TypeScript puede inferir tipos automáticamente

#### **🎨 Para el Diseño**
- **Layout inteligente**: `banner_image` → hero, `image` → thumbnail
- **Responsive automático**: Diferentes tratamientos según el contexto
- **Consistencia visual**: Mismos campos, misma apariencia

#### **🌍 Para Internacionalización**
- **Traducción selectiva**: Solo campos `translatable: true`
- **Fallback inteligente**: Usa códigos técnicos si falta traducción
- **SEO optimizado**: Alt texts y descripciones traducibles

---

## 📋 Contrato de Render

### Endpoint Principal
```http
GET /api/menus/{menu_id}/render?locale=es-ES&with_ui=1
```

**Parámetros:**
- `locale` (requerido): Idioma del menú (ej: `es-ES`, `en-GB`)
- `fallback` (opcional): Idioma de respaldo si falta traducción
- `with_ui=1` (opcional): Incluye el UI manifest para renderizado

---

## 🏗️ Estructura de Respuesta

### Formato General
```json
{
  "id": "menu_id",
  "template": { "slug": "template-name", "version": 1 },
  "locale": "es-ES",
  "ui": { /* UI Manifest */ },
  "data": { /* Contenido del menú */ }
}
```

### UI Manifest (`ui`)
Contiene la información estructural para renderizar el menú:

```json
{
  "layout": "sections",
  "sections": [
    {
      "key": "header",
      "role": "header", 
      "order": 0,
      "display": "hero",
      "labels": {"es-ES": "Cabecera", "en-GB": "Header"},
      "hints": {"icon": "utensils"}
    },
    {
      "key": "starters",
      "role": "course_list",
      "order": 10, 
      "display": "list",
      "labels": {"es-ES": "Entrantes"},
      "hints": {
        "choose_count": 2,
        "scope": "per_table", 
        "show_price": false,
        "icon": "utensils"
      }
    }
  ],
  "catalogs": {
    "allergens": [
      {
        "code": "eggs",
        "icon": "aegg", 
        "labels": {"es-ES": "Huevos", "en-GB": "Eggs"}
      }
    ],
    "currency": {
      "code": "EUR",
      "symbol": "€", 
      "locale": "es-ES"
    }
  }
}
```

### Datos del Menú (`data`)
Contiene el contenido real organizado por secciones:

```json
{
  "header": {"title": "Menú Aralar"},
  "starters": [
    {
      "_id": "ens-mixta",
      "name": "Ensalada Mixta", 
      "allergens": ["milk"]
    }
  ],
  "footer": {
    "price_total": 38.0,
    "vat_percent": 10,
    "vat_included": true
  }
}
```

---

## 🎯 Campos del UI Manifest

### Sección (`sections[]`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `key` | string | Nombre técnico para acceder a `data[key]` |
| `role` | string | Tipo semántico de sección |
| `order` | number | Orden de renderizado (menor = primero) |
| `display` | string | Sugerencia de componente visual |
| `labels` | object | Títulos por idioma |
| `hints` | object | Configuración adicional (opcional) |

### Roles Disponibles (`role`)

| Role | Descripción | Datos Esperados | Campos Típicos |
|------|-------------|-----------------|----------------|
| `header` | Cabecera del menú | `HeaderData` | `title`, `subtitle?`, `banner_image?`, `banner_image_alt?` |
| `course_list` | Lista de platos | `CourseItem[]` | `_id`, `name`, `description?`, `price?`, `image?`, `image_alt?`, `allergens?`, `badges?` |
| `extras` | Lista de extras incluidos | `ExtraItem[]` | `_id`, `text` |
| `legend` | Leyenda o explicación | `{text, items?}` | `text`, `items?` |
| `note` | Nota informativa | `{text}` | `text` |
| `price_footer` | Pie con precio total | `FooterData` | `price_total`, `vat_percent?`, `vat_included?`, `note?` |

### Tipos de Display (`display`)

| Display | Descripción | Uso Recomendado |
|---------|-------------|-----------------|
| `hero` | Componente destacado | Headers principales |
| `list` | Lista vertical | Platos, cursos |
| `bullets` | Lista con viñetas | Extras, incluidos |
| `table` | Tabla estructurada | Comparaciones |
| `grid` | Rejilla de elementos | Galería de platos |
| `legend` | Leyenda de símbolos | Explicación de iconos |
| `footer_price` | Pie de precio | Totales, IVA |

### Hints Disponibles (`hints`)

| Hint | Tipo | Descripción |
|------|------|-------------|
| `choose_count` | number | Cantidad a elegir (ej: "elige 2") |
| `scope` | string | Ámbito: `"per_table"` \| `"per_person"` |
| `show_price` | boolean | Mostrar precios individuales |
| `icon` | string | Icono representativo |

---

## 🧩 Implementación Frontend

### 1. Registry de Componentes (React/TypeScript)

```typescript
// types/menu.ts
export type SectionRole = 
  | "header" 
  | "course_list" 
  | "extras" 
  | "legend" 
  | "note" 
  | "price_footer";

export type DisplayType = 
  | "hero" 
  | "list" 
  | "bullets" 
  | "table" 
  | "grid" 
  | "legend" 
  | "footer_price";

export interface ImageData {
  url: string;
  mime?: string;
  width?: number;
  height?: number;
  size?: number;
}

export interface HeaderData {
  title: string;
  subtitle?: string;
  banner_image?: ImageData;
  banner_image_alt?: string;
}

export interface CourseItem {
  _id: string;
  name: string;
  description?: string;
  price?: number;
  image?: ImageData;
  image_alt?: string;
  allergens?: string[];
  badges?: string[];
}

export interface ExtraItem {
  _id: string;
  text: string;
}

export interface FooterData {
  price_total: number;
  vat_percent?: number;
  vat_included?: boolean;
  note?: string;
}

export interface UiSection {
  key: string;
  role: SectionRole;
  order: number;
  display: DisplayType;
  labels?: Record<string, string>;
  hints?: {
    choose_count?: number;
    scope?: "per_table" | "per_person";
    show_price?: boolean;
    icon?: string;
  };
}

export interface Allergen {
  code: string;
  icon?: string;
  labels?: Record<string, string>;
}

export interface MenuData {
  ui?: {
    layout: string;
    sections: UiSection[];
    catalogs?: {
      allergens?: Allergen[];
      currency?: {
        code: string;
        symbol: string;
        locale: string;
      };
    };
  };
  data: {
    header?: HeaderData;
    [key: string]: CourseItem[] | ExtraItem[] | FooterData | HeaderData | any;
  };
  meta?: {
    title: string;
    summary: string;
  };
  locale: string;
}
```

### 2. Registry de Componentes

```typescript
// components/registry.ts
import { HeaderHero } from './HeaderHero';
import { CourseList } from './CourseList';
import { BulletList } from './BulletList';
import { PriceFooter } from './PriceFooter';
import { Legend } from './Legend';
import { NoteBlock } from './NoteBlock';

export const ROLE_TO_COMPONENT = {
  header: HeaderHero,
  course_list: CourseList,
  extras: BulletList,
  legend: Legend,
  note: NoteBlock,
  price_footer: PriceFooter,
} as const;
```

### 3. Componente Principal de Renderizado

```typescript
// components/MenuRender.tsx
import React from 'react';
import { MenuData, UiSection } from '../types/menu';
import { ROLE_TO_COMPONENT } from './registry';

interface MenuRenderProps {
  payload: MenuData;
}

export function MenuRender({ payload }: MenuRenderProps) {
  // Ordenar secciones por order
  const sections = (payload.ui?.sections || [])
    .slice()
    .sort((a, b) => a.order - b.order);

  return (
    <div className="menu-container">
      {sections.map((section) => {
        const Component = ROLE_TO_COMPONENT[section.role];
        
        if (!Component) {
          console.warn(`No component found for role: ${section.role}`);
          return null;
        }

        // Obtener datos de la sección
        const sectionData = payload.data[section.key];
        
        // Obtener etiqueta en el idioma actual
        const label = section.labels?.[payload.locale] || section.key;

        return (
          <section 
            key={section.key} 
            className={`menu-section menu-section--${section.role}`}
            data-role={section.role}
            data-display={section.display}
          >
            <Component
              keyName={section.key}
              role={section.role}
              display={section.display}
              label={label}
              data={sectionData}
              hints={section.hints}
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

### 4. Componente de Lista de Platos con Alérgenos

```typescript
// components/CourseList.tsx
import React from 'react';
import { Allergen } from '../types/menu';

interface CourseListProps {
  label: string;
  data: Array<{
    _id: string;
    name: string;
    description?: string;
    price?: number;
    allergens?: string[];
  }>;
  hints?: {
    choose_count?: number;
    scope?: "per_table" | "per_person";
    show_price?: boolean;
    icon?: string;
  };
  catalogs?: {
    allergens?: Allergen[];
  };
  locale: string;
}

export function CourseList({ 
  label, 
  data, 
  hints, 
  catalogs, 
  locale 
}: CourseListProps) {
  // Crear mapa de alérgenos para búsqueda rápida
  const allergenMap = new Map<string, Allergen>();
  catalogs?.allergens?.forEach((allergen) => {
    allergenMap.set(allergen.code, allergen);
  });

  // Construir texto de selección
  const getSelectionText = () => {
    if (!hints?.choose_count) return '';
    
    const count = hints.choose_count;
    const scope = hints.scope === 'per_table' ? 'por mesa' : 
                  hints.scope === 'per_person' ? 'por persona' : '';
    
    return `Elegir ${count}${scope ? ` ${scope}` : ''}`;
  };

  return (
    <div className="course-list">
      <header className="course-list__header">
        {hints?.icon && (
          <i 
            className={`icon icon--${hints.icon}`} 
            aria-hidden="true"
          />
        )}
        <h3 className="course-list__title">{label}</h3>
        {hints?.choose_count && (
          <span className="course-list__selection">
            {getSelectionText()}
          </span>
        )}
      </header>

      <ul className="course-list__items">
        {(data || []).map((item) => (
          <li key={item._id} className="course-item">
            <div className="course-item__content">
              <h4 className="course-item__name">{item.name}</h4>
              
              {item.description && (
                <p className="course-item__description">
                  {item.description}
                </p>
              )}
              
              {hints?.show_price && item.price != null && (
                <span className="course-item__price">
                  {item.price}€
                </span>
              )}
            </div>

            {/* Renderizar alérgenos */}
            {Array.isArray(item.allergens) && item.allergens.length > 0 && (
              <div className="course-item__allergens">
                {item.allergens.map((code) => {
                  const allergen = allergenMap.get(code);
                  const allergenLabel = allergen?.labels?.[locale] || code;
                  
                  return (
                    <span 
                      key={code} 
                      className="allergen-badge"
                      title={allergenLabel}
                    >
                      <i 
                        className={`allergen-icon allergen-icon--${allergen?.icon || code}`}
                        aria-hidden="true"
                      />
                      <span className="sr-only">{allergenLabel}</span>
                    </span>
                  );
                })}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### 5. Componente de Pie de Precio

```typescript
// components/PriceFooter.tsx
import React from 'react';

interface PriceFooterProps {
  label: string;
  data: {
    price_total: number;
    vat_percent?: number;
    vat_included?: boolean;
    note?: string;
  };
  catalogs?: {
    currency?: {
      code: string;
      symbol: string;
      locale: string;
    };
  };
}

export function PriceFooter({ label, data, catalogs }: PriceFooterProps) {
  const currency = catalogs?.currency;
  const formatPrice = (price: number) => {
    if (currency) {
      return new Intl.NumberFormat(currency.locale, {
        style: 'currency',
        currency: currency.code,
      }).format(price);
    }
    return `${price}€`;
  };

  return (
    <footer className="price-footer">
      <div className="price-footer__main">
        <span className="price-footer__amount">
          {formatPrice(data.price_total)}
        </span>
        
        {data.vat_percent && (
          <span className="price-footer__vat">
            {data.vat_percent}% I.V.A. {data.vat_included ? 'incluido' : 'no incluido'}
          </span>
        )}
      </div>
      
      {data.note && (
        <p className="price-footer__note">{data.note}</p>
      )}
    </footer>
  );
}
```

---

## 🎨 Estilos CSS Recomendados

```css
/* Estructura base del menú */
.menu-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 1rem;
}

.menu-section {
  margin-bottom: 2rem;
}

/* Lista de platos */
.course-list__header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.course-list__title {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.course-list__selection {
  font-size: 0.875rem;
  color: #666;
  font-style: italic;
}

.course-list__items {
  list-style: none;
  padding: 0;
  margin: 0;
}

.course-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem 0;
  border-bottom: 1px solid #eee;
}

.course-item__name {
  font-size: 1.125rem;
  font-weight: 500;
  margin: 0 0 0.25rem 0;
}

.course-item__description {
  font-size: 0.875rem;
  color: #666;
  margin: 0;
}

/* Alérgenos */
.course-item__allergens {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
  margin-left: 1rem;
}

.allergen-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #f5f5f5;
  border-radius: 50%;
  font-size: 12px;
}

.allergen-icon {
  width: 16px;
  height: 16px;
}

/* Pie de precio */
.price-footer {
  text-align: center;
  padding: 2rem 1rem;
  background: #f9f9f9;
  border-radius: 8px;
}

.price-footer__amount {
  font-size: 2rem;
  font-weight: 700;
  color: #2c5530;
}

.price-footer__vat {
  display: block;
  font-size: 0.875rem;
  color: #666;
  margin-top: 0.25rem;
}

/* Utilidades */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

---

## 🔄 Flujo de Implementación

### 1. **Obtener Datos del Menú**
```typescript
const response = await fetch(`/api/menus/${menuId}/render?locale=es-ES&with_ui=1`);
const menuData = await response.json();
```

### 2. **Renderizar con el Componente**
```tsx
<MenuRender payload={menuData} />
```

### 3. **El Sistema Automáticamente:**
- Ordena las secciones por `order`
- Selecciona el componente correcto según `role`
- Pasa los datos de `data[section.key]`
- Aplica las `hints` para configuración
- Mapea alérgenos usando el catálogo

---

## ✨ Ventajas de Este Enfoque

### **🔧 Flexibilidad**
- **Agnóstico de estructura**: No importa si el menú tiene 3 o 10 secciones
- **Reutilizable**: Los mismos componentes sirven para diferentes tipos de menú
- **Extensible**: Fácil agregar nuevos `roles` y `displays`

### **🌍 Multiidioma**
- **Labels automáticos**: Títulos de sección en el idioma correcto
- **Alérgenos localizados**: Nombres de alérgenos traducidos
- **Fallback inteligente**: Si falta traducción, usa el código

### **🎨 Consistencia**
- **Componentes estandarizados**: Misma apariencia en todos los menús
- **Configuración centralizada**: `hints` controlan comportamiento
- **Accesibilidad**: Screen readers y navegación por teclado

### **⚡ Performance**
- **Renderizado eficiente**: Solo los componentes necesarios
- **Mapas optimizados**: Búsqueda rápida de alérgenos
- **Lazy loading**: Posible cargar secciones bajo demanda

---

## 🚀 Casos de Uso Avanzados

### **Menús Dinámicos**
El sistema soporta menús completamente diferentes sin cambiar código:
- Menú simple (solo header + lista + precio)
- Menú complejo (múltiples cursos + extras + leyendas)
- Menú temático (secciones personalizadas)

### **Personalización por Template**
Cada template puede definir:
- Secciones únicas (`role` personalizado)
- Hints específicos (reglas de selección)
- Catálogos propios (alérgenos, categorías)

### **Integración con Sistemas de Pedidos**
Los `hints` permiten implementar lógica de negocio:
- `choose_count + scope` → Validación de selección
- `show_price` → Cálculo de totales
- `allergens` → Filtros y alertas

## 📝 Mejores Prácticas para Fields.key

### **🔧 Desarrollo Frontend**

#### **1. Validación de Campos**
```typescript
// Validar campos requeridos antes de renderizar
function validateHeaderData(data: any): data is HeaderData {
  return data && typeof data.title === 'string';
}

function validateCourseItem(item: any): item is CourseItem {
  return item && 
         typeof item._id === 'string' && 
         typeof item.name === 'string';
}
```

#### **2. Fallbacks Inteligentes**
```typescript
// Manejo seguro de campos opcionales
function renderCourseImage(item: CourseItem) {
  if (!item.image?.url) return null;
  
  return (
    <img 
      src={item.image.url}
      alt={item.image_alt || item.name}
      width={item.image.width}
      height={item.image.height}
    />
  );
}
```

#### **3. Tipado Defensivo**
```typescript
// Componente que maneja datos inconsistentes
function SafeCourseList({ data }: { data: unknown }) {
  const courses = Array.isArray(data) ? data.filter(validateCourseItem) : [];
  
  if (courses.length === 0) {
    return <div>No hay platos disponibles</div>;
  }
  
  return (
    <ul>
      {courses.map(course => (
        <li key={course._id}>{course.name}</li>
      ))}
    </ul>
  );
}
```

### **🎨 Convenciones de Diseño**

#### **1. Mapeo Automático de Estilos**
```css
/* Estilos basados en field.key */
.course-item[data-has-image="true"] {
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: 1rem;
}

.course-item[data-has-badges="true"] .course-item__name::after {
  content: "🌱"; /* Para badges veganos */
}

.header[data-has-banner="true"] {
  min-height: 400px;
  background-size: cover;
}
```

#### **2. Responsive por Contexto**
```css
/* Banner vs image tienen comportamientos diferentes */
.header__banner-image {
  width: 100%;
  height: 300px;
  object-fit: cover;
}

.course-item__image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
}
```

### **🔍 Debugging y Desarrollo**

#### **1. Inspector de Datos**
```typescript
// Componente de desarrollo para inspeccionar estructura
function DataInspector({ data, sectionKey }: { data: any, sectionKey: string }) {
  if (process.env.NODE_ENV !== 'development') return null;
  
  return (
    <details style={{ margin: '1rem 0', fontSize: '12px' }}>
      <summary>🔍 Debug: {sectionKey}</summary>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </details>
  );
}
```

#### **2. Validación en Desarrollo**
```typescript
// Warnings para campos faltantes comunes
function devWarnings(section: UiSection, data: any) {
  if (process.env.NODE_ENV !== 'development') return;
  
  if (section.role === 'course_list' && Array.isArray(data)) {
    data.forEach((item, index) => {
      if (!item._id) {
        console.warn(`Course item ${index} missing _id in section ${section.key}`);
      }
      if (item.image && !item.image_alt) {
        console.warn(`Course item ${item._id} has image but no image_alt`);
      }
    });
  }
}
```

### **🚀 Optimización y Performance**

#### **1. Lazy Loading de Imágenes**
```typescript
// Carga diferida basada en el contexto
function OptimizedImage({ imageData, context }: { 
  imageData: ImageData, 
  context: 'banner' | 'course' 
}) {
  const loading = context === 'banner' ? 'eager' : 'lazy';
  const priority = context === 'banner';
  
  return (
    <img 
      src={imageData.url}
      loading={loading}
      {...(priority && { fetchPriority: 'high' })}
    />
  );
}
```

#### **2. Memoización Inteligente**
```typescript
// Memo basado en _id para listas grandes
const CourseItem = React.memo(({ item }: { item: CourseItem }) => {
  return (
    <div className="course-item">
      <h4>{item.name}</h4>
      {item.description && <p>{item.description}</p>}
    </div>
  );
}, (prev, next) => prev.item._id === next.item._id);
```

Esta convención de naming y las prácticas asociadas garantizan un desarrollo frontend robusto, mantenible y escalable. 🎯

---

Este sistema proporciona una base sólida y flexible para renderizar cualquier tipo de menú de manera consistente y escalable. 🎉
