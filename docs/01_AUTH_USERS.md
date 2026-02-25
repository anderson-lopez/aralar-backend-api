# Flujos de Autenticación y Gestión de Usuarios

## 1. Flujo de Login

```mermaid
sequenceDiagram
    actor U as Usuario
    participant API as /api/auth
    participant DB as MongoDB

    U->>API: POST /login {email, password}
    API->>DB: Buscar usuario por email
    DB-->>API: Documento del usuario
    API->>API: Verificar contraseña (bcrypt)

    alt Credenciales válidas
        API->>DB: Resolver roles del usuario
        DB-->>API: Permisos efectivos
        API->>API: Generar JWT (access_token + refresh_token)
        API-->>U: 200 {access_token, refresh_token}
    else Credenciales inválidas
        API-->>U: 401 "Invalid email or password"
    end

    Note over U: Rate limit: 5 intentos/minuto
```

**Caso de prueba QA:**
- Login exitoso con credenciales válidas → recibe tokens
- Login con email incorrecto → 401
- Login con password incorrecto → 401
- Login con 6 intentos rápidos → 429 (rate limited)

---

## 2. Ciclo de Vida de Sesión

```mermaid
stateDiagram-v2
    [*] --> Sin_Sesion
    Sin_Sesion --> Autenticado: POST /login (200)
    Autenticado --> Sin_Sesion: POST /logout
    Autenticado --> Sin_Sesion: Token expirado (180 min)
    Autenticado --> Token_Invalidado: Admin invalida token
    Token_Invalidado --> Sin_Sesion: Debe hacer login de nuevo
    Autenticado --> Permisos_Cambiados: Admin cambia roles/permisos
    Permisos_Cambiados --> Sin_Sesion: perm_version no coincide → 401
```

**Caso de prueba QA:**
- Hacer login → usar token → funciona
- Hacer logout → reusar token → 401
- Admin invalida token de otro usuario → ese token deja de funcionar
- Admin cambia rol del usuario → token existente se rechaza (perm_version)

---

## 3. Consultar Información del Usuario Autenticado

```mermaid
sequenceDiagram
    actor U as Usuario
    participant API as /api/auth/me

    U->>API: GET /me (Header: Bearer TOKEN)
    API->>API: Decodificar JWT
    API->>API: Validar blacklist
    API->>API: Validar perm_version

    alt Token válido
        API-->>U: 200 {user_id, email, roles, permissions}
    else Token inválido/expirado
        API-->>U: 401
    end
```

---

## 4. Flujo de Registro

```mermaid
sequenceDiagram
    actor U as Nuevo Usuario
    participant API as /api/auth

    U->>API: POST /register {email, password, name}

    alt Email disponible
        API->>DB: Crear usuario
        API-->>U: 201 {message, user_id}
    else Email ya existe
        API-->>U: 400 "validation_error"
    end
```

**Caso de prueba QA:**
- Registro con email nuevo → 201
- Registro con email duplicado → 400
- Registro sin campos requeridos → 400

---

## 5. Cambio de Contraseña

```mermaid
flowchart TD
    A[Usuario autenticado] --> B{¿Quién cambia?}
    B -->|El propio usuario| C["PUT /auth/change-password<br/>{current_password, new_password}"]
    B -->|Un admin| D["PUT /users/:id/change-password<br/>{new_password}<br/>Permiso: users:change_password"]

    C --> E{¿current_password correcto?}
    E -->|Sí| F[200 Password changed]
    E -->|No| G[400 validation_error]

    D --> F
```

---

## 6. Gestión de Usuarios (Admin)

```mermaid
flowchart LR
    subgraph "CRUD de Usuarios (Admin)"
        CREATE["POST /users<br/>Crear usuario<br/>Permiso: users:create"]
        LIST["GET /users<br/>Listar usuarios<br/>Permiso: users:read"]
        GET["GET /users/:id<br/>Ver detalle<br/>Permiso: users:read"]
    end

    subgraph "Configuración de Acceso"
        ROLES["PUT /users/:id/roles<br/>Asignar roles<br/>Permiso: users:assign_roles"]
        PERMS["PUT /users/:id/permissions<br/>Asignar permisos directos<br/>Permiso: users:assign_permissions"]
        ACT["PUT /users/:id/activate<br/>Activar usuario<br/>Permiso: users:activate"]
        DEACT["PUT /users/:id/deactivate<br/>Desactivar usuario<br/>Permiso: users:activate"]
    end

    CREATE --> ROLES
    CREATE --> PERMS
    ROLES --> ACT
```

---

## 7. Caso de Uso Completo: Admin Crea un Editor

```mermaid
sequenceDiagram
    actor Admin
    participant API

    Note over Admin: Paso 1 — Crear el usuario
    Admin->>API: POST /users {email, password, name}
    API-->>Admin: 201 {id: "user_123"}

    Note over Admin: Paso 2 — Asignar rol "manager"
    Admin->>API: PUT /users/user_123/roles {roles: ["manager"]}
    API-->>Admin: 200 (usuario actualizado)

    Note over Admin: Paso 3 (opcional) — Agregar permiso extra
    Admin->>API: PUT /users/user_123/permissions {permissions_allow: ["menu_templates:create"], permissions_deny: []}
    API-->>Admin: 200 (permisos actualizados)

    Note over Admin: Paso 4 — Verificar
    Admin->>API: GET /users/user_123
    API-->>Admin: 200 {email, roles: ["manager"], permissions_allow: [...]}
```

**Caso de prueba QA:**
- Admin crea usuario → se devuelve ID
- Admin asigna rol → el usuario ahora tiene permisos del rol
- El nuevo usuario hace login → sus permisos incluyen los del rol + allow - deny
- Admin desactiva usuario → el usuario no puede hacer login

---

## 8. Sistema de Permisos (cómo se calculan)

```mermaid
flowchart TD
    R["Roles del usuario<br/>(e.g., manager)"] --> RP["Permisos del rol<br/>(del documento 'roles')"]
    PA["permissions_allow<br/>(permisos extra del usuario)"] --> EFF
    PD["permissions_deny<br/>(permisos denegados)"] --> EFF
    RP --> EFF["Permisos efectivos =<br/>(rol_permisos ∪ allow) − deny"]
    EFF --> JWT["Se incluyen en el JWT<br/>al hacer login"]
    JWT --> VALID["Cada request valida<br/>permisos del JWT"]
```

**Ejemplo:**
- Usuario con rol `manager` tiene: `menus:read`, `menus:create`, `menus:update`, etc.
- Se le agrega `permissions_allow: ["menu_templates:create"]` → ahora también puede crear templates
- Se le agrega `permissions_deny: ["notifications:delete"]` → ya no puede borrar notificaciones

---

## 9. Gestión de Roles y Permisos

```mermaid
flowchart TD
    subgraph "Roles (Admin)"
        LR["GET /roles<br/>Listar roles"]
        CR["POST /roles<br/>Crear rol"]
        UR["PUT /roles/:name<br/>Actualizar rol"]
        DR["DELETE /roles/:name<br/>Eliminar rol"]
    end

    subgraph "Permisos (Admin)"
        LP["GET /roles/permissions<br/>Listar permisos"]
        UP["PUT /roles/permissions/:name<br/>Crear/actualizar permiso"]
    end

    CR -->|"Define nombre + lista de permisos"| UR
    LP -->|"Ver qué permisos existen"| UP
```

### Roles predefinidos del sistema

| Rol | Descripción | Permisos clave |
|-----|-------------|----------------|
| `admin` | Administrador total | Todos los permisos |
| `manager` | Gestión operativa | Menús CRUD, notificaciones CRUD, usuarios lectura |
| `staff` | Personal | Solo lectura de menús y notificaciones |
| `user` | Usuario básico | Solo lectura de menús y notificaciones |

---

## 10. Invalidación de Tokens (Admin)

```mermaid
sequenceDiagram
    actor Admin
    participant API as /api/auth
    participant DB as MongoDB (blacklist)

    Note over Admin: Escenario: empleado despedido, invalidar su token
    Admin->>API: POST /invalidate-token {token: "JWT_DEL_USUARIO", reason: "terminated"}
    API->>DB: Agregar JTI a blacklist
    API-->>Admin: 200 {message, jti, reason}

    Note over Admin: Verificar historial
    Admin->>API: GET /blacklist-history/USER_ID
    API-->>Admin: 200 {tokens: [...], total_count}
```

**Caso de prueba QA:**
- Admin invalida token → el usuario afectado recibe 401 en su siguiente request
- Admin consulta historial de blacklist → ve los tokens invalidados
- Usuario normal intenta invalidar token → 403 (sin permiso)
