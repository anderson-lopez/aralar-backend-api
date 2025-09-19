# Guía de Renderizado de Menús para Frontend

Esta guía explica cómo el frontend debe interpretar y renderizar los menús usando el contrato de la API de Aralar.

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

| Role | Descripción | Datos Esperados |
|------|-------------|-----------------|
| `header` | Cabecera del menú | `{title, subtitle?, date?}` |
| `course_list` | Lista de platos | `[{_id, name, description?, price?, allergens?}]` |
| `extras` | Lista de extras incluidos | `[{_id, text}]` |
| `legend` | Leyenda o explicación | `{text, items?}` |
| `note` | Nota informativa | `{text}` |
| `price_footer` | Pie con precio total | `{price_total, vat_percent, vat_included, note?}` |

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
  data: Record<string, any>;
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

Este sistema proporciona una base sólida y flexible para renderizar cualquier tipo de menú de manera consistente y escalable. 🎉
