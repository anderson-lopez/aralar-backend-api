# Historial — Backend (Aralar API)

> **Lectura obligatoria al inicio de una nueva sesión** (sea humana o agente).
> Resume las decisiones arquitectónicas vigentes, el estado del último
> trabajo y las convenciones del repo. Si añades trabajo, agrega una entrada
> NUEVA arriba con fecha. **No borres las anteriores.**

---

## Convenciones del repo

### Source y mirror
Este backend existe en **dos rutas** que deben mantenerse byte-idénticas:

- `C:\Users\Anderson\Desktop\aralar-backend-api\` ← source
- `C:\Users\Anderson\Desktop\ligthNetwork\aralarBackendApi\` ← mirror (el que despliega Render)

Cualquier cambio en uno debe propagarse al otro antes de commitear ambos.
Los commits suelen ser idénticos en mensaje pero los SHA diferirán (es ok).

### Tests
- **pytest + mongomock** (Mongo en memoria por test) + **pytest-cov**.
- Comando completo: `.venv/Scripts/python.exe -m pytest -q` (~40s).
- Rápido sin cobertura: `pytest -q --no-cov` (~12s).
- Cobertura objetivo: **≥70% en `aralar/services/`**, **≥60% en `aralar/api/`**, **≥65% global**.
- Markers: `@pytest.mark.unit | integration | e2e`. Úsalos siempre.
- Fixtures globales en `tests/conftest.py`: `app`, `client`, `db`, `auth_headers`.
- Factories en `tests/factories.py`: `make_menu`, `seed_menu`, `make_image`, `make_template`, `seed_template`. **Úsalas en vez de dicts inline.**

### Permisos (relevante para tests)
- `auth_headers()` por defecto da TODOS los permisos del sistema (`DEFAULT_PERMISSIONS` en `conftest.py`).
- Si añades un endpoint con un permiso nuevo (ej. `notifications:export`), agrégalo a `DEFAULT_PERMISSIONS`.
- **OJO con el guión vs underscore**: `menu_templates:*` (con underscore en el código y permisos), NO `menu-templates:*` (con guión, que es solo el URL prefix).

### Endpoints clave de auth (lo que esperan los tests)
- `POST /auth/login` valida **solo length** de password (no fortaleza).
- `POST /users` y `POST /auth/register` validan fortaleza (mayús/minús/número).
- Si `/auth/login` devuelve 403 con `error: no_permissions`, el usuario existe pero no tiene roles → frontend debe distinguir esto de 401.

### Reglas anti-softlock activas
Están en `aralar/services/users_service.py` y `aralar/api/users/blueprint.py`:

1. Nadie puede eliminarse ni desactivarse a sí mismo.
2. Nadie puede eliminar/desactivar al **último admin activo** (helper `is_last_active_admin`).
3. `update_user_roles` rechaza quitar `admin` al último admin activo.

**No revertir.** El frontend (admin) también lo bloquea visualmente.

### Reglas de merge `common ↔ locales`
En `menus_service._deep_merge_sections`:
- Cuando `common` tiene un valor no vacío en una clave, **gana common** sobre `locales`.
- Solo si `common` está vacío/None, `locales` rellena.
- Esto arregla un bug de "imagen vieja del locale pisa la imagen nueva del common" cuando un campo pasa de `translatable=true` a `false`.

`update_common` además llama a `_strip_common_keys_from_locales` para limpiar las claves que ya viven en `common` de los `locales.<lang>.data`.

---

## Cambios por sesión

### 2026-05-28 → 2026-06-03 — Suite de tests + reglas anti-softlock + cleanup

**Tests añadidos** (`tests/`): **233 tests / 74% cobertura global** (`72%` services, `68%` api).

| Bloque | Archivos | Notas |
|---|---|---|
| A — Services | `test_menus_service.py`, `test_menu_templates_service.py`, `test_roles_service.py` | Pure-unit + integration con mongomock. |
| B — Endpoints | `test_menus_endpoints.py`, `test_menu_templates_endpoints.py` | E2E vía `client`. Happy + 400/401/403/404/409. |
| C — Auth/Permisos/Externos | `test_auth.py`, `test_permissions.py`, `test_users.py`, `test_notifications.py`, `test_uploads.py`, `test_i18n.py` | `boto3` y `requests.post` (DeepL/Google) mockeados. |

**Backend code changes:**
- `is_last_active_admin()` en `users_service.py` (cuenta admins activos en BD).
- Guards en `blueprint.py`: `delete_user`, `deactivate_user`, `update_user_roles`.
- `_deep_merge_sections` endurecido para que common gane sobre locales.
- `_strip_common_keys_from_locales` en `update_common`.

**Pendientes** (no scope de esta sesión):
- Subir `notifications_service.py` (61%), `token_blacklist_service.py` (43%), `uploads_service.py` (54%) si se quiere más cobertura.
- El `aralar/api/notifications/controllers.py` envuelve `abort(404)` del service en `try/except → abort(500)` (bug latente: el 404 del service se reporta como 500).

---

## Cómo verificar el estado en tu primera vuelta

```bash
cd C:\Users\Anderson\Desktop\ligthNetwork\aralarBackendApi
.venv/Scripts/python.exe -m pytest -q     # debe dar 233 passed
git status                                # debe estar limpio
git log -1 --oneline                      # último commit conocido en main
```

Si pytest no corre, falta `.venv`:
```bash
python -m venv .venv
.venv/Scripts/pip.exe install -r requirements.txt
```

El mirror (`aralar-backend-api`) debe quedar idéntico tras cualquier cambio.
