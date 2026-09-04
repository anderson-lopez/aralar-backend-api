# Reseñas de Google — guía de frontend

Sección de opiniones de clientes en la landing: estrellas, texto, nombre y foto del autor.

> **Resumen en una línea:** la landing pide `GET /api/google-reviews/public` y pinta las
> tarjetas. Todo lo demás (extracción, moderación, sincronización) pasa en el backend.

---

## 1. Qué problema resuelve

Google no ofrece ningún widget oficial embebible ni una API abierta que devuelva todas las
reseñas de un local. Las que existen o devuelven 5 como máximo (Places API), o exigen una
solicitud de acceso manual de semanas (Business Profile API), o son de pago.

La solución implementada: el backend extrae las reseñas de Google, las **modera** (para que no
salga nada negativo o inapropiado) y las guarda en Mongo. La landing solo consume un endpoint
propio, rápido y siempre disponible — **aunque Google esté caído, la sección sigue pintando**.

---

## 2. Lo único imprescindible para el frontend

### `GET /api/google-reviews/public`

Endpoint **abierto** (sin token). Devuelve solo reseñas aprobadas.

| Query param | Tipo | Descripción |
|---|---|---|
| `tenant_id` | string | Opcional. Filtra por restaurante. |
| `limit` | int | Opcional. Máximo de tarjetas a devolver. |

```jsonc
{
  "items": [
    {
      "rating": 5,
      "text": "Excelente comida y trato inmejorable.",
      "author_name": "Ana García",
      "author_photo_url": "https://lh3.googleusercontent.com/a/ana-garcia=s120",
      "author_profile_url": "https://www.google.com/maps/contrib/1000000000000001",
      "published_at": "2026-07-01T10:00:00",
      "is_featured": false
    }
  ],
  "total": 12,          // total de aprobadas (NO se ve afectado por `limit`)
  "average_rating": 4.7 // media de las aprobadas; null si no hay ninguna
}
```

**Notas de consumo:**
- `total` es el total real de aprobadas, no `items.length`. Sirve para pintar *"12 opiniones"*
  aunque solo muestres 6 tarjetas.
- `average_rating` viene redondeado a 2 decimales, o `null` si aún no hay reseñas.
- El orden ya viene resuelto por el backend: primero las que tienen orden manual asignado, y
  el resto por fecha descendente. **No reordenes en el cliente.**
- `is_featured` es una marca opcional por si quieres destacar visualmente alguna tarjeta.

### ⚠️ Atribución obligatoria

Google exige que, al mostrar sus reseñas, se acredite al autor. En la práctica:

- Muestra **`author_name`** y, si hay espacio, **`author_photo_url`**.
- Enlaza a **`author_profile_url`** cuando exista.
- No recortes ni edites el texto de la reseña.

`author_photo_url` puede venir `null` o caducar con el tiempo (son URLs de Google, no las
alojamos nosotros). **Prevé un fallback de iniciales** en un círculo de color:

```jsx
{r.author_photo_url
  ? <img src={r.author_photo_url} alt={r.author_name} onError={mostrarIniciales} />
  : <Iniciales nombre={r.author_name} />}
```

---

## 3. Cómo llega el dato (contexto, no hace falta implementarlo)

```
Google Maps ──sync (1×/día)──► Mongo ──moderación──► /public ──► Landing
```

1. Un job diario (`scripts/sync_google_reviews.py`, por cron) extrae las reseñas.
2. Cada reseña pasa por **moderación automática**:

   | Caso | Estado | Por qué |
   |---|---|---|
   | Texto + `rating >= 4` | `approved` | Se publica sola |
   | Texto + `rating < 4` | `pending` | Es una crítica real: decide un humano |
   | **Sin texto** (solo estrellas) | `rejected` | No hay tarjeta que pintar |

3. Lo que queda `pending` se revisa a mano desde el panel.
4. La landing solo ve lo `approved`.

> **Ojo con las reseñas sin texto:** en Google son ~**44%** del total (medido sobre las
> 590 reseñas reales del local). Se descartan solas para que la bandeja de moderación no
> se llene de items impublicables, pero **siguen guardadas** y se pueden recuperar
> cambiando su `status`.

**Regla importante:** una decisión humana nunca se revierte sola. Si alguien rechaza una
reseña a mano, las sincronizaciones posteriores refrescan su texto pero **no la vuelven a
publicar**.

---

## 4. Panel de administración

Todos estos endpoints requieren token + permiso.

| Verbo | Ruta | Permiso | Para qué |
|---|---|---|---|
| `GET` | `/api/google-reviews` | `google_reviews:read` | Listado con filtros (bandeja) |
| `GET` | `/api/google-reviews/{id}` | `google_reviews:read` | Detalle |
| `POST` | `/api/google-reviews/sync` | `google_reviews:sync` | Sincronizar bajo demanda |
| `POST` | `/api/google-reviews/manual` | `google_reviews:create` | Alta manual |
| `PUT` | `/api/google-reviews/{id}` | `google_reviews:update` | Destacar / ordenar |
| `PUT` | `/api/google-reviews/{id}/moderate` | `google_reviews:moderate` | Aprobar / rechazar |
| `DELETE` | `/api/google-reviews/{id}` | `google_reviews:delete` | Eliminar |

### Bandeja de moderación

```http
GET /api/google-reviews?status=pending&limit=20
```

Filtros disponibles: `tenant_id`, `provider`, `status` (`approved`/`pending`/`rejected`),
`rating` (1-5), `skip`, `limit`. Respuesta paginada: `{items, total, skip, limit}`.

### Aprobar o rechazar

```http
PUT /api/google-reviews/{id}/moderate
{ "status": "approved" }   // approved | pending | rejected
```

Deja registro de quién y cuándo en `moderation`, y marca `moderation.auto = false` para que el
sync no lo pise.

### Destacar u ordenar

```http
PUT /api/google-reviews/{id}
{ "is_featured": true, "display_order": 1 }
```

`display_order` menor = más arriba. Las que no lo tienen van al final, ordenadas por fecha.

> Este endpoint **solo** acepta `is_featured` y `display_order`. Mandar `rating`, `text` o
> `status` devuelve **422**: el contenido lo manda el origen y el estado se cambia por
> `/moderate`.

### Alta manual

Útil para cargar reseñas a mano (o mientras se configura el scraping):

```http
POST /api/google-reviews/manual
{
  "tenant_id": "aralar",
  "rating": 5,
  "text": "Excelente",
  "author": { "name": "Ana", "photo_url": null, "profile_url": null }
}
```

Pasa por la misma moderación automática que el resto.

### Sincronizar

```http
POST /api/google-reviews/sync
→ { "fetched": 190, "created": 190, "updated": 0,
    "auto_approved": 87, "auto_rejected": 81, "pending": 22, "errors": [] }
```

**Devuelve 200 incluso si falla el origen** — el detalle va en `errors`. Es deliberado: un
fallo de red no debe romper el panel, y los datos guardados no se tocan. Si `errors` no está
vacío, muéstralo como aviso, no como error fatal.

---

## 5. Propuesta de UI para el panel

**Pantalla "Opiniones"** con tres pestañas por `status`:

```
┌─────────────────────────────────────────────────────────┐
│  Opiniones          [ Sincronizar ahora ]  [ + Manual ] │
│  ─────────────────────────────────────────────────────  │
│  ( Pendientes 3 )  ( Publicadas 12 )  ( Rechazadas 1 )  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ (foto)  Ana García            ★★★★★   1 jul 2026   │ │
│  │ "Excelente comida y trato inmejorable."            │ │
│  │                          [ Rechazar ] [ Aprobar ]  │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

Detalles que ayudan:
- El contador de **Pendientes** como badge — es lo único que requiere acción.
- En "Publicadas", sustituir los botones por un toggle de **destacar** y un campo de **orden**.
- El botón *Sincronizar ahora* muestra el resumen devuelto (`created`/`updated`) en un toast.
- Las reseñas rechazadas no se borran: se pueden recuperar cambiando su `status`.

---

## 6. Estados y errores

| Código | Cuándo |
|---|---|
| `200` | OK (incluye `/sync` con errores dentro de `errors`) |
| `201` | Reseña manual creada |
| `400` | Id malformado |
| `401` | Falta token |
| `403` | Falta el permiso |
| `404` | La reseña no existe |
| `409` | Alta manual con un `external_id` que ya existe |
| `422` | Payload inválido (p. ej. `rating` fuera de 1-5, o campo no permitido en `PUT`) |

---

## 7. Puesta en marcha (backend)

1. Correr migraciones: `docker-compose exec api python scripts/migrate.py`
   (crea la colección `google_reviews` y los permisos `google_reviews:*`).
2. En `.env`, elegir el origen:
   - `GOOGLE_REVIEWS_PROVIDER=manual` → sin red; las reseñas se cargan desde el panel.
   - `GOOGLE_REVIEWS_PROVIDER=scraper` → además, pegar la URL del local en
     `GOOGLE_MAPS_PLACE_URL`.
3. Ajustar `GOOGLE_REVIEWS_AUTO_APPROVE_MIN_RATING` (por defecto `4`) y
   `GOOGLE_REVIEWS_MAX_PAGES` (por defecto `10` ≈ 190 reseñas; ~19 por página).
4. Arrancar con `docker-start.bat` (o `.sh`, o `make docker-init`).

**La primera carga es automática.** Los scripts de arranque ejecutan
`sync_google_reviews.py --if-empty` justo después de migrar y sembrar: si la colección
está vacía trae las reseñas, y en los arranques siguientes no vuelve a consultar a
Google. Así, al levantar Docker por primera vez ya hay datos que pintar **sin configurar
ningún cron**. Si falla (falta la URL, Google caído) solo imprime un aviso — **la API
arranca igualmente**.

Para mantenerlas al día en producción, un cron diario:
```
30 4 * * *  docker-compose exec -T api python scripts/sync_google_reviews.py
```
O a mano en cualquier momento: `make docker-sync-reviews` (o el botón *Sincronizar
ahora* del panel).

**Para comprobar la extracción sin base de datos ni app levantada:**

```bash
python scripts/sync_google_reviews.py --dry-run --url "https://www.google.com/maps/place/..."
```

Imprime las reseñas por pantalla y cuántas se publicarían, sin escribir nada.

Los permisos ya se asignan solos: `admin` recibe todos y `manager` recibe
`read`/`moderate`/`sync`.
