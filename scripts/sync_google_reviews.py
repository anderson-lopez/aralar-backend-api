"""Sincroniza las reseñas de Google hacia la colección `google_reviews`.

Pensado para ejecutarse por cron (o a mano). Es idempotente: re-ejecutarlo no
duplica reseñas porque el upsert va por `(tenant_id, provider, external_id)`.

    docker-compose exec api python scripts/sync_google_reviews.py
    docker-compose exec api python scripts/sync_google_reviews.py --tenant aralar

    # `--if-empty` solo sincroniza si la colección está vacía. Es lo que llaman
    # docker-start.bat/.sh en cada arranque: la primera vez trae las reseñas y en
    # los siguientes arranques no toca Google.
    docker-compose exec api python scripts/sync_google_reviews.py --if-empty

    # cron sugerido para mantenerlas al día (una vez al día sobra para una landing)
    # 30 4 * * *  docker-compose exec -T api python scripts/sync_google_reviews.py

Sale con código 1 si hubo errores, para que cron lo detecte. Un fallo del origen
NO borra ni altera lo ya guardado: la landing sigue sirviendo el último estado bueno.

Para **probar la extracción sin base de datos ni app levantada**:

    python scripts/sync_google_reviews.py --dry-run --url "https://www.google.com/maps/place/..."

`--dry-run` extrae y muestra las reseñas por pantalla sin escribir nada.
`--dump-raw <archivo>` guarda la respuesta cruda sin procesar; sirve para corregir el
mapa de índices de `_parse_review` si Google cambia el formato.
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient

# Ensure project root (one level up) is on sys.path when running from scripts/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from aralar.config import BaseConfig as Config  # noqa: E402
from aralar.core.reviews.providers import (  # noqa: E402
    GoogleMapsScraperProvider,
    ReviewsProviderError,
    get_provider,
)
from aralar.repositories.google_reviews_repo import GoogleReviewsRepo  # noqa: E402
from aralar.services.google_reviews_service import GoogleReviewsService  # noqa: E402

SUMMARY_LINE = (
    "[sync] fetched={fetched} created={created} updated={updated} "
    "auto_approved={auto_approved} auto_rejected={auto_rejected} pending={pending}"
)


def _config_dict():
    """`get_provider` espera algo con `.get()`, igual que `app.config`."""
    return {
        key: getattr(Config, key)
        for key in dir(Config)
        if key.isupper() and not key.startswith("_")
    }


def _scraper_from(cfg) -> GoogleMapsScraperProvider:
    return GoogleMapsScraperProvider(
        feature_id=cfg.get("GOOGLE_MAPS_FEATURE_ID", ""),
        place_url=cfg.get("GOOGLE_MAPS_PLACE_URL", ""),
        locale=cfg.get("GOOGLE_REVIEWS_LOCALE", "es"),
        max_pages=cfg.get("GOOGLE_REVIEWS_MAX_PAGES", 10),
        timeout=cfg.get("GOOGLE_REVIEWS_TIMEOUT", 20),
        user_agent=cfg.get("GOOGLE_REVIEWS_USER_AGENT", ""),
    )


def dump_raw(cfg, destination: str) -> int:
    provider = _scraper_from(cfg)
    if not provider.feature_id:
        print("[sync] ERROR: falta GOOGLE_MAPS_FEATURE_ID o GOOGLE_MAPS_PLACE_URL")
        return 1
    try:
        raw = provider._request_page("")
        payload = provider._load_payload(raw)
    except ReviewsProviderError as exc:
        print(f"[sync] ERROR: {exc}")
        return 1
    with open(destination, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"[sync] respuesta cruda guardada en {destination}")
    return 0


def dry_run(cfg, tenant: str, min_rating: int) -> int:
    """Extrae y muestra las reseñas por pantalla **sin tocar Mongo**.

    Sirve para comprobar de un vistazo que la URL del local es correcta y que el
    parseo saca los campos esperados, antes de montar nada más.
    """
    provider = _scraper_from(cfg)
    if not provider.feature_id:
        print("[sync] ERROR: falta la URL del local.")
        print("        Pasa --url '<url de Google Maps>' o rellena GOOGLE_MAPS_PLACE_URL en .env")
        return 1

    print(f"[sync] feature_id={provider.feature_id} locale={provider.locale}")
    print("[sync] consultando Google...")
    try:
        reviews = provider.fetch_reviews(tenant_id=tenant)
    except ReviewsProviderError as exc:
        print(f"[sync] ERROR: {exc}")
        return 1

    if not reviews:
        print("[sync] La peticion funciono pero no se extrajo ninguna resena.")
        print("       Suele significar que Google cambio el formato de la respuesta.")
        print("       Guarda la respuesta cruda con --dump-raw captura.json y revisa")
        print("       el mapa de indices de _parse_review en aralar/core/reviews/providers.py")
        return 1

    print(f"[sync] {len(reviews)} resenas extraidas\n")
    for r in reviews:
        stars = "*" * r["rating"] + "." * (5 - r["rating"])
        author = r["author"].get("name") or "(sin nombre)"
        published = r["published_at"].date().isoformat() if r["published_at"] else "(sin fecha)"
        text = (r["text"] or "").replace("\n", " ")
        if len(text) > 100:
            text = text[:97] + "..."
        print(f"  [{stars}] {author}  -  {published}")
        print(f"           {text or '(sin texto)'}")
        if not r["author"].get("photo_url"):
            print("           (sin foto de autor)")
        print()

    # Se usa la moderación real del service para que la previsión coincida
    # exactamente con lo que haría un sync de verdad.
    svc = GoogleReviewsService(None, min_rating=min_rating)
    buckets: dict[str, int] = {}
    for r in reviews:
        status, _ = svc._auto_moderate(r)
        buckets[status] = buckets.get(status, 0) + 1

    ratings = [r["rating"] for r in reviews]
    print(f"[sync] total={len(reviews)} | media={sum(ratings) / len(ratings):.2f}")
    print(f"[sync]   {buckets.get('approved', 0):>4} se publicarian (con texto y >= {min_rating} estrellas)")
    print(f"[sync]   {buckets.get('pending', 0):>4} quedarian para revision manual (con texto, pocas estrellas)")
    print(f"[sync]   {buckets.get('rejected', 0):>4} descartadas por no tener texto (solo estrellas)")
    print("[sync] dry-run: no se ha escrito nada en la base de datos")
    return 0


def main() -> int:
    load_dotenv()

    # Las reseñas traen emojis y acentos que la consola de Windows (cp1252) no sabe
    # codificar: sin esto un `print` reventaría con UnicodeEncodeError.
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, OSError):
        pass

    parser = argparse.ArgumentParser(description="Sincroniza reseñas de Google")
    parser.add_argument(
        "--tenant",
        default=os.getenv("DEFAULT_TENANT_ID", "aralar"),
        help="tenant al que pertenecen las reseñas (default: aralar)",
    )
    parser.add_argument(
        "--url",
        metavar="URL",
        help="URL del local en Google Maps (sustituye a GOOGLE_MAPS_PLACE_URL del .env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="extrae y muestra las reseñas por pantalla sin escribir en la base de datos",
    )
    parser.add_argument(
        "--if-empty",
        action="store_true",
        help="solo sincroniza si el tenant aun no tiene resenas (para el arranque)",
    )
    parser.add_argument(
        "--dump-raw",
        metavar="ARCHIVO",
        help="guarda la respuesta cruda del scraper y termina (para depurar el parseo)",
    )
    args = parser.parse_args()

    cfg = _config_dict()
    if args.url:
        # Pasar la URL por línea de comandos implica querer el scraper.
        cfg["GOOGLE_MAPS_PLACE_URL"] = args.url
        cfg["GOOGLE_MAPS_FEATURE_ID"] = ""
        cfg["GOOGLE_REVIEWS_PROVIDER"] = "scraper"

    if args.dump_raw:
        return dump_raw(cfg, args.dump_raw)

    if args.dry_run:
        return dry_run(cfg, args.tenant, cfg.get("GOOGLE_REVIEWS_AUTO_APPROVE_MIN_RATING", 4))

    provider = get_provider(cfg)

    try:
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=10000)
        db = client.get_default_database()
        repo = GoogleReviewsRepo(db)

        # `--if-empty` es lo que permite llamar a este script en cada arranque sin
        # castigar a Google: la primera vez llena la tabla y las siguientes no hace nada.
        if args.if_empty:
            existing = repo.count({"tenant_id": args.tenant})
            if existing:
                print(f"[sync] '{args.tenant}' ya tiene {existing} resenas: nada que hacer")
                return 0
            print(f"[sync] '{args.tenant}' no tiene resenas todavia: sincronizando...")
    except Exception as exc:  # noqa: BLE001 - sin Mongo no se puede ni comprobar
        print(f"[sync] ERROR: no se pudo conectar a MongoDB: {exc}")
        return 1

    print(f"[sync] provider={provider.name} tenant={args.tenant}")

    if provider.name == "manual":
        print("[sync] NOTA: provider 'manual' no consulta ningun origen remoto.")
        print("       Para traer resenas de Google pon GOOGLE_REVIEWS_PROVIDER=scraper")
        print("       y GOOGLE_MAPS_PLACE_URL=<url del local> en el .env")

    svc = GoogleReviewsService(
        repo, provider=provider, min_rating=Config.GOOGLE_REVIEWS_AUTO_APPROVE_MIN_RATING
    )
    result = svc.sync(args.tenant)

    print(SUMMARY_LINE.format(**result))
    if result["errors"]:
        for err in result["errors"]:
            print(f"[sync] ERROR: {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
