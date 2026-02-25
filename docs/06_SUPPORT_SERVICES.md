# Servicios de Soporte: Uploads, Traducciones (i18n) y Catálogos

## 1. Uploads (Subida de Imágenes)

### ¿Para qué sirve?

Los menús pueden incluir imágenes (banners, fotos de platos). El sistema usa **S3/MinIO** como almacenamiento. Hay dos formas de subir archivos: mediante **URLs presignadas** (recomendado para frontend) o **subida directa** por el backend.

---

### Flujo con URL Presignada (recomendado)

```mermaid
sequenceDiagram
    actor Editor
    participant API as /api/uploads
    participant S3 as S3 / MinIO

    Note over Editor: 1. Solicitar URL presignada
    Editor->>API: POST /presign {filename: "banner.webp", mime: "image/webp"}
    API->>S3: Generar URL presignada (PUT)
    S3-->>API: URL firmada (expira en minutos)
    API-->>Editor: {upload_url, public_url, key}

    Note over Editor: 2. Subir archivo directamente a S3
    Editor->>S3: PUT upload_url (body: archivo binario)<br/>Headers: Content-Type + x-amz-acl: public-read
    S3-->>Editor: 200 OK

    Note over Editor: 3. Usar public_url en el menú
    Editor->>API: POST /menus {common: {header: {banner_image: {url: public_url, ...}}}}
```

### Flujo con Proxy (para testing)

```mermaid
sequenceDiagram
    actor Editor
    participant API as /api/uploads
    participant S3 as S3 / MinIO

    Editor->>API: POST /proxy-put (multipart: file + upload_url + content_type)
    API->>S3: PUT binario a upload_url
    S3-->>API: 200 OK + ETag
    API-->>Editor: {message: "ok", etag}
```

### Subida Directa (sin presigned)

```mermaid
sequenceDiagram
    actor Editor
    participant API as /api/uploads
    participant S3 as S3 / MinIO

    Editor->>API: POST /direct (multipart: file, filename, mime)
    API->>S3: put_object directamente
    S3-->>API: OK
    API-->>Editor: {upload_url, public_url, key}
```

### Endpoints de Uploads

| Método | Ruta | Descripción | Permiso |
|--------|------|-------------|---------|
| POST | `/presign` | Obtener URL presignada | `menus:update` |
| POST | `/proxy-put` | Proxy de subida (testing) | `menus:update` |
| POST | `/direct` | Subida directa al bucket | `menus:update` |
| GET | `/presign-info` | Info de uso de presigned URLs | Público |
| GET | `/bucket-exists-boto` | Verificar que el bucket existe | `menus:update` |

**Casos de prueba QA:**
- Solicitar presign → recibe `upload_url` y `public_url` válidas
- Subir archivo a `upload_url` con headers correctos → 200
- Subir archivo sin `x-amz-acl: public-read` → puede fallar
- Subir archivo con `Content-Type` diferente al del presign → puede fallar
- Subida directa → recibe `public_url` accesible
- `GET /presign-info` → documentación de uso

---

## 2. Traducciones (i18n)

### ¿Para qué sirve?

El sistema soporta **múltiples idiomas** para los menús. El servicio de traducción permite:
- Traducir textos automáticamente (usando DeepL u otro proveedor)
- Detectar el idioma de un texto
- Gestionar glosarios personalizados por tenant (para que términos como "txakoli" no se traduzcan mal)

---

### Flujo de Traducción

```mermaid
sequenceDiagram
    actor Editor
    participant API as /api/i18n
    participant Provider as DeepL / Proveedor
    participant DB as MongoDB (glossaries)

    Note over Editor: 1. Traducir textos
    Editor->>API: POST /translate {texts: ["Gazpacho", "Tortilla"], source_lang: "es", target_lang: "en-GB", tenant_id: "aralar"}
    API->>DB: Buscar glosario para aralar es→en
    DB-->>API: Glosario (pares de términos)
    API->>Provider: Traducir con glosario aplicado
    Provider-->>API: ["Gazpacho", "Spanish omelette"]
    API-->>Editor: {translations: [...], source_lang, target_lang}
```

### Gestión de Glosarios

```mermaid
sequenceDiagram
    actor Admin
    participant API as /api/i18n

    Note over Admin: Crear/actualizar glosario
    Admin->>API: POST /glossaries {<br/>  tenant_id: "aralar",<br/>  source_lang: "es",<br/>  target_lang: "en",<br/>  pairs: [<br/>    {source: "txakoli", target: "txakoli"},<br/>    {source: "pintxo", target: "pintxo"},<br/>    {source: "carrillera", target: "beef cheek"}<br/>  ]<br/>}
    API-->>Admin: {tenant_id, source_lang, target_lang, version, pairs}

    Note over Admin: Consultar glosario actual
    Admin->>API: GET /glossaries/current?tenant_id=aralar&source_lang=es&target_lang=en
    API-->>Admin: {pairs: [...], version}
```

### Detección de Idioma

```mermaid
sequenceDiagram
    actor Editor
    participant API as /api/i18n

    Editor->>API: POST /detect {texts: ["Menú del día", "Daily menu"]}
    API-->>Editor: {detections: [{lang: "es", confidence: 0.98}, {lang: "en", confidence: 0.95}]}
```

### Endpoints de i18n

| Método | Ruta | Descripción | Permiso |
|--------|------|-------------|---------|
| POST | `/translate` | Traducir textos con glosario | `menus:update` |
| POST | `/detect` | Detectar idioma | `menus:update` |
| POST | `/glossaries` | Crear/actualizar glosario | `menus:update` |
| GET | `/glossaries/current` | Obtener glosario vigente | `menus:update` |

**Casos de prueba QA:**
- Traducir texto sencillo → respuesta correcta
- Traducir con glosario → términos del glosario se respetan
- Traducir sin glosario (`use_glossary: false`) → traducción estándar
- Detectar idioma → devuelve código de idioma + confianza
- Crear glosario → se guarda con versión
- Actualizar glosario → incrementa versión
- Consultar glosario inexistente → 404

---

## 3. Catálogos

### ¿Para qué sirve?

Proporciona datos de referencia estáticos que el frontend necesita, como la lista de **alérgenos europeos** con sus iconos y etiquetas multi-idioma.

---

### Catálogo de Alérgenos

```mermaid
sequenceDiagram
    actor Cliente
    participant API as GET /catalogs/allergens

    Cliente->>API: ?locale=es-ES
    API-->>Cliente: 14 alérgenos europeos con iconos y labels

    Note over API: Datos estáticos definidos<br/>en el código del servidor
```

**Endpoint único:**

| Método | Ruta | Descripción | Permiso |
|--------|------|-------------|---------|
| GET | `/allergens` | Lista de 14 alérgenos europeos | Público |

**Parámetro opcional:** `locale` — si se especifica, agrega campo `label` en ese idioma.

**Casos de prueba QA:**
- `GET /catalogs/allergens` → 14 alérgenos con `labels` multi-idioma
- `GET /catalogs/allergens?locale=es-ES` → incluye campo `label` en español
- `GET /catalogs/allergens?locale=en-GB` → incluye campo `label` en inglés
- Los iconos corresponden a los códigos de alérgeno (e.g., `gluten` → `agluten`)

---

## 4. Diagrama de Integración de Servicios de Soporte

```mermaid
flowchart TD
    subgraph "Editor crea un menú"
        A["1. Subir imagen<br/>POST /uploads/presign"] --> B["2. PUT imagen a S3"]
        B --> C["3. Crear menú con public_url<br/>POST /menus"]
        C --> D["4. Rellenar locale ES<br/>PUT /menus/:id/locales/es-ES"]
        D --> E["5. Traducir a EN automáticamente<br/>POST /i18n/translate"]
        E --> F["6. Rellenar locale EN<br/>PUT /menus/:id/locales/en-GB"]
    end

    subgraph "Cliente ve el menú"
        G["7. Render del menú<br/>GET /menus/:id/render?locale=es-ES"] --> H["8. Cargar alérgenos<br/>GET /catalogs/allergens?locale=es-ES"]
    end

    F --> G
```

Este diagrama muestra cómo los tres servicios de soporte se integran en el flujo principal de creación y visualización de menús.
