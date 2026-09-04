from flask_smorest import Blueprint, abort
from flask import current_app
from bson import ObjectId
from ...repositories.menu_services_repo import MenuServicesRepo
from ...repositories.menus_repo import MenusRepo
from ...services.menu_services_service import MenuServicesService
from ...schemas.menu_service_schemas import (
    MenuServiceCreateSchema,
    MenuServiceUpdateSchema,
    MenuServiceSchema,
    MenuServiceListSchema,
    MenuServiceListQueryArgs,
    MenuServiceMessageSchema,
    MenuServicePublicListSchema,
    MenuServicePublicQueryArgs,
)
from ...core.security import require_permissions


blp = Blueprint("menu_services", "menu_services", description="Menu services (Otros servicios) endpoints")


def _abort_if_invalid_id(_id: str):
    try:
        ObjectId(_id)
    except Exception:
        abort(400, message="invalid id")


def get_svc():
    db = current_app.mongo_db
    return MenuServicesService(MenuServicesRepo(db))


@blp.route("", methods=["POST"])
@require_permissions("menu_services:create")
@blp.arguments(MenuServiceCreateSchema)
@blp.response(201, MenuServiceSchema)
@blp.alt_response(400, schema=MenuServiceMessageSchema)
@blp.alt_response(409, schema=MenuServiceMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def create_service(body):
    svc = get_svc()
    res = svc.create(body)
    if isinstance(res, dict) and res.get("error"):
        abort(400, message=res["error"])
    if isinstance(res, dict) and res.get("conflict"):
        abort(409, message=res["conflict"])
    return res


@blp.route("", methods=["GET"])
@require_permissions("menu_services:read")
@blp.arguments(MenuServiceListQueryArgs, location="query")
@blp.response(200, MenuServiceListSchema)
@blp.doc(security=[{"bearerAuth": []}])
def list_services(query_args):
    svc = get_svc()
    return svc.list(query_args)


@blp.route("/public", methods=["GET"])
@blp.arguments(MenuServicePublicQueryArgs, location="query")
@blp.response(200, MenuServicePublicListSchema)
def public_services(query):
    """Servicios activos para pintar la sección pública "Otros servicios"."""
    svc = get_svc()
    return svc.public_list(tenant_id=query.get("tenant_id"), locale=query.get("locale"))


@blp.route("/<service_id>", methods=["GET"])
@require_permissions("menu_services:read")
@blp.response(200, MenuServiceSchema)
@blp.alt_response(404, schema=MenuServiceMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def get_service(service_id):
    _abort_if_invalid_id(service_id)
    svc = get_svc()
    doc = svc.get(service_id)
    if not doc:
        abort(404, message="not found")
    return doc


@blp.route("/<service_id>", methods=["PUT"])
@require_permissions("menu_services:update")
@blp.arguments(MenuServiceUpdateSchema)
@blp.response(200, MenuServiceSchema)
@blp.alt_response(404, schema=MenuServiceMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def update_service(body, service_id):
    """Actualiza un servicio. El `slug` es inmutable (ver MenuServicesService.update).

    Al desactivar un servicio con menús, la respuesta incluye `affected_menus`
    con cuántos quedan ocultos, para poder avisar en el panel.
    """
    _abort_if_invalid_id(service_id)
    db = current_app.mongo_db
    svc = get_svc()
    res = svc.update(service_id, body, menus_repo=MenusRepo(db))
    if res is None:
        abort(404, message="not found")
    return res


@blp.route("/<service_id>", methods=["DELETE"])
@require_permissions("menu_services:delete")
@blp.response(200, MenuServiceMessageSchema)
@blp.alt_response(404, schema=MenuServiceMessageSchema)
@blp.alt_response(409, schema=MenuServiceMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def delete_service(service_id):
    """Elimina un servicio. Bloquea con 409 si algún menú lo referencia."""
    _abort_if_invalid_id(service_id)
    db = current_app.mongo_db
    svc = get_svc()
    res = svc.delete(service_id, menus_repo=MenusRepo(db))
    if res is None:
        abort(404, message="not found")
    if isinstance(res, dict) and res.get("conflict"):
        abort(409, message=res["conflict"])
    return {"message": "ok"}
