from flask_smorest import Blueprint, abort
from flask import request, current_app
from ...services.i18n_service import I18nService
from ...core.i18n.providers import get_provider
from ...core.security import require_permissions
from ...schemas.i18n_schemas import (
    TranslateRequestSchema,
    TranslateResponseSchema,
    DetectRequestSchema,
    DetectResponseSchema,
    GlossaryUpsertSchema,
    GlossaryQuerySchema,
    GlossaryResponseSchema,
    MessageSchema,
)

blp = Blueprint("i18n", "i18n", description="Translation API")


def get_svc():
    db = current_app.mongo_db
    provider = get_provider(current_app.config)
    provider_name = current_app.config.get("I18N_PROVIDER", "deepl")
    return I18nService(db, provider, provider_name)


@blp.route("/translate", methods=["POST"])
@require_permissions("menus:update")
@blp.arguments(TranslateRequestSchema)
@blp.response(200, TranslateResponseSchema)
@blp.alt_response(422, schema=MessageSchema, description="Validation error")
@blp.doc(security=[{"bearerAuth": []}])
def translate(body):
    texts = body.get("texts") or []
    src = body.get("source_lang")
    tgt = body.get("target_lang")
    tenant_id = body.get("tenant_id")
    use_gloss = body.get("use_glossary", True)

    db = current_app.mongo_db
    glossary = None
    if use_gloss:
        glossary = db["glossaries"].find_one(
            {"tenant_id": tenant_id, "source_lang": (src or "es").split("-")[0], "target_lang": tgt}
        )

    svc = get_svc()
    res = svc.translate_batch(tenant_id, texts, src, tgt, glossary)
    return res


@blp.route("/detect", methods=["POST"])
@require_permissions("menus:update")
@blp.arguments(DetectRequestSchema)
@blp.response(200, DetectResponseSchema)
@blp.alt_response(422, schema=MessageSchema, description="Validation error")
@blp.doc(security=[{"bearerAuth": []}])
def detect(body):
    texts = body.get("texts") or []
    svc = get_svc()
    res = svc.detect(texts)
    return res


@blp.route("/glossaries", methods=["POST"])
@require_permissions("menus:update")
@blp.arguments(GlossaryUpsertSchema)
@blp.response(200, GlossaryResponseSchema)
@blp.alt_response(422, schema=MessageSchema, description="Validation error")
@blp.doc(security=[{"bearerAuth": []}])
def upsert_glossary(body):
    tenant_id = body.get("tenant_id")
    src = body.get("source_lang")
    tgt = body.get("target_lang")
    pairs = body.get("pairs") or []

    db = current_app.mongo_db
    gcol = db["glossaries"]
    doc = gcol.find_one_and_update(
        {"tenant_id": tenant_id, "source_lang": src, "target_lang": tgt},
        {"$set": {"pairs": pairs}, "$inc": {"version": 1}},
        upsert=True,
        return_document=True,
    )
    # si doc es None (pyMongo con upsert puede devolver None sin ReturnDocument.after), devuelve básico
    if not doc:
        return {"tenant_id": tenant_id, "source_lang": src, "target_lang": tgt, "version": 1, "pairs": pairs}
    return {
        "tenant_id": doc.get("tenant_id"),
        "source_lang": doc.get("source_lang"),
        "target_lang": doc.get("target_lang"),
        "version": doc.get("version", 1),
        "pairs": doc.get("pairs", []),
    }


@blp.route("/glossaries/current", methods=["GET"])
@require_permissions("menus:update")
@blp.arguments(GlossaryQuerySchema, location="query")
@blp.response(200, GlossaryResponseSchema)
@blp.alt_response(404, schema=MessageSchema)
@blp.alt_response(422, schema=MessageSchema, description="Validation error")
@blp.doc(security=[{"bearerAuth": []}])
def current_glossary(query):
    tenant_id = query.get("tenant_id")
    src = query.get("source_lang")
    tgt = query.get("target_lang")
    db = current_app.mongo_db
    g = db["glossaries"].find_one({"tenant_id": tenant_id, "source_lang": src, "target_lang": tgt})
    if not g:
        abort(404, message="not found")
    return {
        "tenant_id": g.get("tenant_id"),
        "source_lang": g.get("source_lang"),
        "target_lang": g.get("target_lang"),
        "version": g.get("version", 1),
        "pairs": g.get("pairs", []),
    }
