from flask_smorest import Blueprint
from flask import request
from ...extensions import mongo_client

blp = Blueprint("catalogs", "catalogs", url_prefix="/api/catalogs", description="Public catalogs")

# Fuente: o bien fija (constante en código), o leída desde un template "global" por tenant.
# Aquí devolvemos una lista fija (idéntica a la usada en tus templates UI.catalogs.allergens)
ALLERGENS = [
    {"code": "gluten", "icon": "agluten", "labels": {"es-ES": "Gluten", "en-GB": "Gluten"}},
    {
        "code": "crustaceans",
        "icon": "acrusta",
        "labels": {"es-ES": "Crustáceos", "en-GB": "Crustaceans"},
    },
    {"code": "eggs", "icon": "aegg", "labels": {"es-ES": "Huevos", "en-GB": "Eggs"}},
    {"code": "fish", "icon": "afish", "labels": {"es-ES": "Pescado", "en-GB": "Fish"}},
    {"code": "peanuts", "icon": "apeanut", "labels": {"es-ES": "Cacahuetes", "en-GB": "Peanuts"}},
    {"code": "soy", "icon": "asoy", "labels": {"es-ES": "Soja", "en-GB": "Soy"}},
    {"code": "milk", "icon": "amilk", "labels": {"es-ES": "Leche/Lactosa", "en-GB": "Milk"}},
    {"code": "nuts", "icon": "anuts", "labels": {"es-ES": "Frutos secos", "en-GB": "Tree nuts"}},
    {"code": "celery", "icon": "acelery", "labels": {"es-ES": "Apio", "en-GB": "Celery"}},
    {"code": "mustard", "icon": "amustard", "labels": {"es-ES": "Mostaza", "en-GB": "Mustard"}},
    {"code": "sesame", "icon": "asesame", "labels": {"es-ES": "Sésamo", "en-GB": "Sesame"}},
    {"code": "sulfites", "icon": "asulfite", "labels": {"es-ES": "Sulfitos", "en-GB": "Sulphites"}},
    {"code": "lupin", "icon": "alupin", "labels": {"es-ES": "Altramuces", "en-GB": "Lupin"}},
    {"code": "molluscs", "icon": "amollusc", "labels": {"es-ES": "Moluscos", "en-GB": "Molluscs"}},
]


@blp.route("/allergens", methods=["GET"])
def catalogs_allergens():
    # opcional: ?locale=es-ES para proyectar sólo ese idioma
    locale = request.args.get("locale")
    items = ALLERGENS
    if locale:
        # proyectar labels en un solo idioma + fallback a code
        items = [{**a, "label": a.get("labels", {}).get(locale, a["code"])} for a in ALLERGENS]
    return {"items": items}
