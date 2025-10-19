"""
Migración 012: Backfill de i18n y locales en notificaciones

- Si solo existe `content`, crear `locales.es-ES.data.content`
- Asegurar `i18n.default_locale` y `i18n.locales` (incluye claves de `locales`)
- Marcar `locales.es-ES.meta.migrated_from_content=True` cuando aplique
- No eliminar `content` (compatibilidad)
"""

from datetime import datetime


def up(db):
    print("[012] Iniciando backfill de i18n y locales en notifications...")
    col = db["notifications"]
    updated = 0

    # Trabajar sobre todos los documentos para idempotencia general
    cursor = col.find({})
    for doc in cursor:
        set_ops = {}
        locales_map = doc.get("locales") or {}

        # Si no hay locales y hay content legacy, migrar a es-ES
        if (not locales_map) and isinstance(doc.get("content"), str) and doc.get("content").strip():
            set_ops["locales.es-ES"] = {
                "data": {"content": doc.get("content")},
                "meta": {"migrated_from_content": True},
            }
            # Refrescar mapa en memoria para construir i18n.locales
            locales_map = {"es-ES": set_ops["locales.es-ES"]}

        # Construir i18n si falta o está incompleto
        i18n = doc.get("i18n") or {}
        default_locale = i18n.get("default_locale")
        if not default_locale:
            # Elegir es-ES si existe en locales, sino primera clave de locales, sino es-ES por defecto
            if "es-ES" in locales_map:
                default_locale = "es-ES"
            elif locales_map:
                try:
                    default_locale = next(iter(locales_map.keys()))
                except Exception:
                    default_locale = "es-ES"
            else:
                default_locale = "es-ES"
            set_ops["i18n.default_locale"] = default_locale

        # Asegurar lista de locales en i18n
        locales_list = set(i18n.get("locales") or [])
        locales_list.update(list(locales_map.keys()))
        if default_locale and default_locale not in locales_list:
            locales_list.add(default_locale)
        set_ops["i18n.locales"] = sorted(list(locales_list)) if locales_list else [default_locale]

        if set_ops:
            set_ops["updated_at"] = datetime.utcnow()
            res = col.update_one({"_id": doc["_id"]}, {"$set": set_ops})
            if res.modified_count > 0:
                updated += 1
                print(f"[012] ✓ Actualizado {_id_str(doc)}")

    print(f"[012] Backfill completado. Documentos actualizados: {updated}")


def down(db):
    print("[012 rollback] Revirtiendo backfill de i18n y locales en notifications...")
    col = db["notifications"]
    reverted = 0

    # Quitar solo los campos creados por esta migración (locales.es-ES migrados y i18n si fue creado por ausencia)
    cursor = col.find({"locales.es-ES.meta.migrated_from_content": True})
    for doc in cursor:
        unset_ops = {"locales.es-ES": ""}
        set_ops = {"updated_at": datetime.utcnow()}
        # Intentar revertir i18n si parece haber sido añadido por la migración (heurística: falta default original)
        i18n = doc.get("i18n") or {}
        if not i18n.get("default_locale"):
            unset_ops["i18n"] = ""
        res = col.update_one({"_id": doc["_id"]}, {"$unset": unset_ops, "$set": set_ops})
        if res.modified_count > 0:
            reverted += 1
            print(f"[012 rollback] ✓ Revertido en {_id_str(doc)}")

    print(f"[012 rollback] Rollback completado. Documentos revertidos: {reverted}")


def _id_str(doc):
    try:
        return str(doc.get("_id"))
    except Exception:
        return "<unknown-id>"
