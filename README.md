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

## 🛠️ Instalación en Windows

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd aralar-api
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
copy .env.example .env
```

Edita el archivo `.env` con tus configuraciones:
```env
FLASK_ENV=development
SECRET_KEY=tu_clave_secreta_aqui
JWT_SECRET_KEY=tu_jwt_secret_aqui
MONGO_URI=mongodb://localhost:27017/aralar
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
RATE_LIMIT_DEFAULT=100/hour
SECURE_COOKIES=false
SEED_ADMIN_EMAIL=admin@aralar.local
SEED_ADMIN_PASSWORD=TuPasswordSegura123!
SEED_ADMIN_FULLNAME="Admin Aralar"
```

### 5. Configurar MongoDB

#### Opción A: MongoDB Local
1. Descargar e instalar [MongoDB Community Server](https://www.mongodb.com/try/download/community)
2. Iniciar el servicio MongoDB
3. Crear la base de datos `aralar`

#### Opción B: Docker (Recomendado)
```bash
docker-compose up -d mongo
```

### 6. Inicializar la base de datos
```bash
python scripts/seed.py
```

Este script creará:
- Índices necesarios
- Catálogo de permisos
- Roles base (admin, manager, staff)
- Usuario administrador inicial

## 🚀 Ejecutar la aplicación

### Desarrollo
```bash
# Activar entorno virtual
.venv\Scripts\activate

# Ejecutar con Flask (desarrollo)
flask --app aralar.app run --debug

# O ejecutar con Python
python -m flask --app aralar.app run --debug
```

### Producción
```bash
# Con Gunicorn
gunicorn -c gunicorn.conf.py wsgi:app

# Con Docker
docker-compose up --build
```

## 📚 Documentación de la API

Una vez ejecutando la aplicación, accede a:
- **Swagger UI**: http://localhost:5000/api/docs/swagger-ui
- **ReDoc**: http://localhost:5000/api/docs/redoc
- **OpenAPI JSON**: http://localhost:5000/api/docs/openapi.json

## 🔐 Endpoints Principales

### Autenticación
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/me` - Información del usuario actual

### Usuarios
- `POST /api/users` - Crear usuario (requiere permisos)
- `GET /api/users` - Listar usuarios (requiere permisos)
- `PUT /api/users/{id}/roles` - Asignar roles (requiere permisos)
- `PUT /api/users/{id}/permissions` - Asignar permisos (requiere permisos)

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