from bson import ObjectId
from flask import current_app
from flask_jwt_extended import get_jwt_identity
from flask_smorest import Blueprint, abort

from ...core.reviews.providers import get_provider
from ...core.security import require_permissions
from ...repositories.google_reviews_repo import GoogleReviewsRepo
from ...schemas.google_review_schemas import (
    GoogleReviewCreateSchema,
    GoogleReviewListQueryArgs,
    GoogleReviewListSchema,
    GoogleReviewMessageSchema,
    GoogleReviewModerateSchema,
    GoogleReviewPublicListSchema,
    GoogleReviewPublicQueryArgs,
    GoogleReviewSchema,
    GoogleReviewSyncResultSchema,
    GoogleReviewUpdateSchema,
)
from ...services.google_reviews_service import GoogleReviewsService

blp = Blueprint(
    "google_reviews", "google_reviews", description="Google reviews endpoints"
)


def _abort_if_invalid_id(_id: str):
    try:
        ObjectId(_id)
    except Exception:
        abort(400, message="invalid id")


def get_svc():
    db = current_app.mongo_db
    cfg = current_app.config
    return GoogleReviewsService(
        GoogleReviewsRepo(db),
        provider=get_provider(cfg),
        min_rating=cfg.get("GOOGLE_REVIEWS_AUTO_APPROVE_MIN_RATING", 4),
    )


@blp.route("/public", methods=["GET"])
@blp.arguments(GoogleReviewPublicQueryArgs, location="query")
@blp.response(200, GoogleReviewPublicListSchema)
def public_reviews(query):
    """Reseñas aprobadas para la landing, con media y total.

    Endpoint abierto: no lleva decorador de auth a propósito.
    """
    svc = get_svc()
    return svc.public_list(tenant_id=query.get("tenant_id"), limit=query.get("limit"))


@blp.route("/sync", methods=["POST"])
@require_permissions("google_reviews:sync")
@blp.response(200, GoogleReviewSyncResultSchema)
@blp.doc(security=[{"bearerAuth": []}])
def sync_reviews():
    """Sincroniza desde el provider configurado.

    Devuelve 200 incluso si el provider falla: el detalle va en `errors` y los
    datos ya guardados no se tocan, de modo que la landing nunca se queda vacía
    por un fallo de red o un cambio de formato en el origen.
    """
    svc = get_svc()
    tenant_id = current_app.config.get("DEFAULT_TENANT_ID", "aralar")
    return svc.sync(tenant_id)


@blp.route("", methods=["GET"])
@require_permissions("google_reviews:read")
@blp.arguments(GoogleReviewListQueryArgs, location="query")
@blp.response(200, GoogleReviewListSchema)
@blp.doc(security=[{"bearerAuth": []}])
def list_reviews(query_args):
    svc = get_svc()
    return svc.list(query_args)


@blp.route("/manual", methods=["POST"])
@require_permissions("google_reviews:create")
@blp.arguments(GoogleReviewCreateSchema)
@blp.response(201, GoogleReviewSchema)
@blp.alt_response(409, schema=GoogleReviewMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def create_manual_review(body):
    svc = get_svc()
    res = svc.create_manual(body)
    if isinstance(res, dict) and res.get("conflict"):
        abort(409, message=res["conflict"])
    return res


@blp.route("/<review_id>", methods=["GET"])
@require_permissions("google_reviews:read")
@blp.response(200, GoogleReviewSchema)
@blp.alt_response(404, schema=GoogleReviewMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def get_review(review_id):
    _abort_if_invalid_id(review_id)
    svc = get_svc()
    doc = svc.get(review_id)
    if not doc:
        abort(404, message="not found")
    return doc


@blp.route("/<review_id>", methods=["PUT"])
@require_permissions("google_reviews:update")
@blp.arguments(GoogleReviewUpdateSchema)
@blp.response(200, GoogleReviewSchema)
@blp.alt_response(404, schema=GoogleReviewMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def update_review(body, review_id):
    """Edita solo presentación (`is_featured`, `display_order`)."""
    _abort_if_invalid_id(review_id)
    svc = get_svc()
    res = svc.update(review_id, body)
    if res is None:
        abort(404, message="not found")
    return res


@blp.route("/<review_id>/moderate", methods=["PUT"])
@require_permissions("google_reviews:moderate")
@blp.arguments(GoogleReviewModerateSchema)
@blp.response(200, GoogleReviewSchema)
@blp.alt_response(400, schema=GoogleReviewMessageSchema)
@blp.alt_response(404, schema=GoogleReviewMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def moderate_review(body, review_id):
    """Aprueba o rechaza a mano. Marca la decisión como humana para que las
    siguientes sincronizaciones no la pisen."""
    _abort_if_invalid_id(review_id)
    svc = get_svc()
    res = svc.moderate(review_id, body["status"], user_id=get_jwt_identity())
    if res is None:
        abort(404, message="not found")
    if isinstance(res, dict) and res.get("error"):
        abort(400, message=res["error"])
    return res


@blp.route("/<review_id>", methods=["DELETE"])
@require_permissions("google_reviews:delete")
@blp.response(200, GoogleReviewMessageSchema)
@blp.alt_response(404, schema=GoogleReviewMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def delete_review(review_id):
    _abort_if_invalid_id(review_id)
    svc = get_svc()
    res = svc.delete(review_id)
    if res is None:
        abort(404, message="not found")
    return {"message": "ok"}
