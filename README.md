# Aralar API

Una API REST moderna construida con Flask para gestión de usuarios, roles y permisos con autenticación JWT.

## 🚀 Características

- **Autenticación JWT** con tokens de acceso y refresh
- **Sistema de roles y permisos** granular y flexible
- **Rate limiting** para prevenir abuso
- **Seguridad** con CORS, Talisman y validación de datos
- **Base de datos MongoDB** con repositorios estructurados
- **Documentación automática** con OpenAPI/Swagger
- **Logging estructurado** con structlog
- **Dockerizado** para desarrollo y producción

## 📋 Requisitos Previos

- Python 3.8+
- MongoDB (local o Docker)
- Git

## 🛠️ Instalación y Despliegue

### 🐳 Opción A: Docker (Recomendado)

La forma más rápida y sencilla de ejecutar la aplicación:

#### 1. Clonar el repositorio

```bash
git clone <tu-repositorio>
cd aralar-api
```

#### 2. Inicio rápido con Docker

**En Windows:**
```bash
docker-start.bat
```

**En Linux/macOS:**
```bash
chmod +x docker-start.sh
./docker-start.sh
```

**O manualmente:**
```bash
# Copiar configuración de ejemplo
copy .env.example .env  # Windows
cp .env.example .env    # Linux/macOS

# Editar .env con tus configuraciones (ver sección de variables de entorno)

# Construir e iniciar servicios
docker-compose up --build -d

# Inicializar base de datos
docker-compose exec api python scripts/migrate.py
docker-compose exec api python scripts/seed.py
```

#### 3. Verificar que todo funciona

- **API**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/api/docs/swagger-ui
- **MongoDB**: localhost:27017

### 💻 Opción B: Instalación Local (Desarrollo)

#### 1. Requisitos previos
- Python 3.8+
- MongoDB (local o Docker)
- Git

#### 2. Configurar entorno

```bash
# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Instalar dependencias
pip install -r requirements.txt
```

#### 3. Configurar variables de entorno

```bash
copy .env.example .env
```

**Para desarrollo local, cambiar en `.env`:**
```env
FLASK_ENV=development
MONGO_URI=mongodb://localhost:27017/aralar
```

#### 4. Configurar MongoDB local

1. Descargar e instalar [MongoDB Community Server](https://www.mongodb.com/try/download/community)
2. Iniciar el servicio MongoDB
3. Crear la base de datos `aralar`

#### 5. Inicializar la base de datos

```bash
python scripts/migrate.py
python scripts/seed.py
```

#### 6. Ejecutar la aplicación

```bash
# Desarrollo
flask --app aralar.app run --debug

# Producción local
gunicorn -c gunicorn.conf.py wsgi:app
```

## 🔧 Variables de Entorno

Edita el archivo `.env` con tus configuraciones:

```env
# Configuración de Flask
FLASK_ENV=production  # o 'development' para desarrollo local
SECRET_KEY=tu_clave_secreta_super_segura_aqui
JWT_SECRET_KEY=tu_jwt_secret_key_aqui

# Base de datos MongoDB
MONGO_URI=mongodb://mongo:27017/aralar  # Para Docker
# MONGO_URI=mongodb://localhost:27017/aralar  # Para desarrollo local

# CORS - Orígenes permitidos
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Seguridad
SECURE_COOKIES=false  # true en producción con HTTPS
TALISMAN_FORCE_HTTPS=false  # true en producción

# Datos del administrador inicial
SEED_ADMIN_EMAIL=admin@aralar.local
SEED_ADMIN_PASSWORD=TuPasswordSegura123!
SEED_ADMIN_FULLNAME="Admin Aralar"
```

## 🐳 Comandos Docker Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f api
docker-compose logs -f mongo

# Reiniciar servicios
docker-compose restart

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes (¡cuidado! elimina datos de BD)
docker-compose down -v

# Reconstruir imágenes
docker-compose build --no-cache

# Ejecutar comandos dentro del contenedor
docker-compose exec api python scripts/seed.py
docker-compose exec mongo mongosh aralar
```

## 📚 Documentación de la API

Una vez ejecutando la aplicación, accede a:

- **Swagger UI**: http://localhost:8000/api/docs/swagger-ui
- **ReDoc**: http://localhost:8000/api/docs/redoc
- **OpenAPI JSON**: http://localhost:8000/api/docs/openapi.json

## 🔐 Endpoints Principales

### Autenticación

- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/me` - Información del usuario actual

### Usuarios

- `POST /api/users` - Crear usuario (requiere permisos)
- `GET /api/users` - Listar usuarios (requiere permisos)
- `PUT /api/users/{id}/roles` - Asignar roles (requiere permisos)
- `PUT /api/users/{id}/permissions` - Asignar permisos (requiere permisos)

## 🍽️ Pasos recomendados: de cero a un menú publicado

Orden operativo con endpoints. Se asume que tu usuario tiene los permisos RBAC indicados entre paréntesis.

### A) Definir Template (editor/admin)

- Crear template (draft)
  - `POST /api/menu-templates` (perm: `menu_templates:create`)
  - Body (ejemplo):

```json
{
  "name": "Seasonal Menu",
  "slug": "seasonal-menu",
  "tenant_id": "aralar",
  "sections": [
    { "key": "starters", "schema": { "type": "array" } }
  ]
}
```

- Iterar/editar mientras sea draft
  - `PUT /api/menu-templates/{template_id}` (perm: `menu_templates:update`)

- Publicar template (versión v1)
  - `POST /api/menu-templates/{template_id}/publish` (perm: `menu_templates:publish`)
  - Devuelve un nuevo id publicado (o publica v1 si era draft). A partir de aquí tienes `{slug, version}` estables para crear menús.

### B) Crear Menú (editor/admin)

- Crear menú usando el template publicado
  - `POST /api/menus` (perm: `menus:create`)
  - Body mínimo:

```json
{
  "tenant_id": "aralar",
  "template_slug": "seasonal-menu",
  "template_version": 1,
  "status": "draft",
  "common": { }
}
```

- Configurar disponibilidad (opcional pero recomendable)
  - `PUT /api/menus/{menu_id}/availability` (perm: `menus:update`)

```json
{
  "timezone": "Europe/Madrid",
  "days_of_week": ["THU", "FRI"],
  "date_ranges": [{ "start": "2025-09-01", "end": "2025-12-31" }]
}
```

### C) Cargar traducciones (editor/traductor)

- Añadir/editar traducción por idioma
  - `PUT /api/menus/{menu_id}/locales/es-ES` (perm: `menus:update`)
  - Body:

```json
{ "data": { "...solo campos traducibles..." } }
```

Repite para `en-GB`, etc.

### D) Publicar por idioma (editor/admin)

- Publicar locale
  - `POST /api/menus/{menu_id}/publish/es-ES` (perm: `menus:publish`)
  - Opcional: repetir para otros idiomas.

A partir de aquí el público puede ver el menú ES cuando esté disponible según Availability.

### E) Consumo público (usuarios anónimos)

- Descubrir qué menús hay activos hoy (o una fecha)
  - `GET /api/menus/public/available?locale=es-ES&tz=Europe/Madrid`
  - Devuelve un array de menús elegibles (IDs, metadatos).

- Renderizar un menú para ese locale (con fallback opcional)
  - `GET /api/menus/{menu_id}/render?locale=es-ES&fallback=en-GB`
  - Devuelve el JSON final listo para UI (títulos, secciones, platos, precios…).

Tu frontend público puede:
- Pedir `/public/available` y mostrar un selector, o
- Si solo hay un menú activo, ir directo a `/render`.

### Notas rápidas

- `/render` no hace feature-merge con el template; usa solo el contenido del menú (ya validado cuando lo guardas).
- Si cambias el template (nueva versión), los menús existentes no cambian; los próximos menús deben apuntar a la nueva versión.
- Si editas contenido no traducible (`common`) o una traducción publicada, `/render` reflejará el cambio sin volver a publicar (puedes exigir re-publicación si lo prefieres).

## 🏗️ Estructura del Proyecto

```
aralar-api/
├── aralar/                 # Paquete principal
│   ├── api/               # Endpoints y controladores
│   │   ├── auth/          # Autenticación
│   │   └── users/         # Gestión de usuarios
│   ├── core/              # Funcionalidades centrales
│   │   ├── logging.py     # Configuración de logs
│   │   └── security.py    # Decoradores de seguridad
│   ├── docs/              # Documentación OpenAPI
│   ├── repositories/      # Acceso a datos
│   ├── schemas/           # Validación con Marshmallow
│   ├── services/          # Lógica de negocio
│   ├── app.py            # Factory de la aplicación
│   ├── config.py         # Configuraciones
│   └── extensions.py     # Inicialización de extensiones
├── scripts/               # Scripts utilitarios
│   └── seed.py           # Inicialización de datos
├── tests/                 # Tests unitarios
├── .env.example          # Variables de entorno ejemplo
├── docker-compose.yml    # Configuración Docker
├── gunicorn.conf.py      # Configuración Gunicorn
├── pyproject.toml        # Dependencias del proyecto
├── requirements.txt      # Dependencias pip
└── wsgi.py              # Punto de entrada WSGI
```

## 🧪 Ejecutar Tests

```bash
# Activar entorno virtual
.venv\Scripts\activate

# Ejecutar tests
python -m pytest tests/ -v
```

## 🔧 Desarrollo

### Agregar nuevos endpoints

1. Crear controlador en `aralar/api/{modulo}/`
2. Definir blueprint en `blueprint.py`
3. Registrar en `aralar/api/routes.py`
4. Agregar schemas en `aralar/schemas/`

### Sistema de permisos

- Los permisos se definen en `scripts/seed.py`
- Usar decoradores `@require_permissions()` o `@require_roles()`
- Los permisos efectivos se calculan: `(permisos_rol + allow) - deny`

## 🐛 Solución de Problemas

### Error de conexión a MongoDB

- Verificar que MongoDB esté ejecutándose
- Revisar la variable `MONGO_URI` en `.env`
- Para Docker: `docker-compose logs mongo`

### Error de importación

- Verificar que el entorno virtual esté activado
- Reinstalar dependencias: `pip install -r requirements.txt`

### Error de permisos JWT

- Verificar que el usuario tenga los roles/permisos necesarios
- Revisar que el token JWT sea válido
- Ejecutar `python scripts/seed.py` para recrear datos iniciales

## 📝 Notas de Seguridad

- Cambiar `SECRET_KEY` y `JWT_SECRET_KEY` en producción
- Usar HTTPS en producción (`TALISMAN_FORCE_HTTPS=true`)
- Configurar `CORS_ORIGINS` específicamente para tu frontend
- Revisar límites de rate limiting según tu caso de uso

## 🤝 Contribuir

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request
