"""
Migración 013 — Sincroniza el nuevo permiso `menus:archive` con la colección de
permisos y el rol `admin`.

Contexto
--------
El endpoint `POST /menus/<id>/archive` usa `@require_permissions("menus:archive")`,
pero ese permiso no existía en `DEFAULT_PERMISSIONS`, por lo que ningún rol lo
tenía y todas las peticiones devolvían 403 Forbidden.

Esta migración:
1. Ejecuta `apply_catalog(db)` — inserta `menus:archive` en `permissions`
   (y en los roles que lo incluyan) de forma idempotente.

Es segura de re-ejecutar.
"""
from aralar.catalog.role_catalog import apply_catalog


def up(db):
    apply_catalog(db)
