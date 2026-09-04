"""Lógica de negocio de las reseñas de Google.

Tres responsabilidades: sincronizar desde el provider, moderar (automática +
humana) y servir el listado público de la landing.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from ..core.reviews.providers import ReviewsProviderError

STATUS_APPROVED = "approved"
STATUS_PENDING = "pending"
STATUS_REJECTED = "rejected"
VALID_STATUSES = (STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED)


class GoogleReviewsService:
    # Contador del resumen de `sync` al que suma cada estado automático.
    _SUMMARY_KEY = {
        STATUS_APPROVED: "auto_approved",
        STATUS_REJECTED: "auto_rejected",
        STATUS_PENDING: "pending",
    }

    def __init__(self, repo, provider=None, min_rating: int = 4):
        """`provider` es opcional para poder testear el service aislado; el
        blueprint y el script de sync siempre lo inyectan."""
        self.repo = repo
        self.provider = provider
        self.min_rating = int(min_rating)

    # -- sincronización ----------------------------------------------------

    def sync(self, tenant_id: str) -> dict:
        """Trae reseñas del provider y las persiste de forma idempotente.

        **Nunca lanza.** Si el provider falla se devuelve el resumen con `errors`
        y los datos ya guardados quedan intactos: la landing sigue sirviendo el
        último estado bueno aunque Google cambie el formato o bloquee la petición.
        """
        summary = {
            "fetched": 0,
            "created": 0,
            "updated": 0,
            "auto_approved": 0,
            "auto_rejected": 0,
            "pending": 0,
            "errors": [],
        }
        if self.provider is None:
            summary["errors"].append("no provider configured")
            return summary

        try:
            incoming = self.provider.fetch_reviews(tenant_id=tenant_id)
        except ReviewsProviderError as exc:
            summary["errors"].append(str(exc))
            return summary
        except Exception as exc:  # noqa: BLE001 - el sync jamás debe tumbar el proceso
            summary["errors"].append(f"unexpected provider failure: {exc}")
            return summary

        provider_name = getattr(self.provider, "name", "unknown")
        summary["fetched"] = len(incoming)

        for item in incoming:
            try:
                created = self._upsert(tenant_id, provider_name, item, summary)
            except Exception as exc:  # noqa: BLE001 - una reseña rota no aborta el lote
                summary["errors"].append(f"could not store review: {exc}")
                continue
            if created is None:
                continue

        return summary

    def _upsert(self, tenant_id: str, provider_name: str, item: dict, summary: dict):
        external_id = item.get("external_id")
        if not external_id:
            return None

        existing = self.repo.get_by_external_id(tenant_id, provider_name, external_id)
        content = {
            "rating": item.get("rating"),
            "text": item.get("text") or "",
            "language": item.get("language"),
            "author": item.get("author") or {},
            "published_at": item.get("published_at"),
        }

        if existing is None:
            status, reason = self._auto_moderate(content)
            doc = {
                "tenant_id": tenant_id,
                "provider": provider_name,
                "external_id": external_id,
                **content,
                "status": status,
                "moderation": {"auto": True, "reason": reason, "by": None, "at": None},
                "is_featured": False,
                "display_order": None,
            }
            self.repo.insert(doc)
            summary["created"] += 1
            summary[self._SUMMARY_KEY[status]] += 1
            return True

        patch = dict(content)

        # La decisión humana manda: si alguien moderó a mano, el sync refresca el
        # contenido pero NO puede devolver a la landing algo que se rechazó.
        human_decided = not (existing.get("moderation") or {}).get("auto", True)
        if not human_decided:
            status, reason = self._auto_moderate(content)
            patch["status"] = status
            patch["moderation"] = {"auto": True, "reason": reason, "by": None, "at": None}

        self.repo.update(str(existing["_id"]), patch)
        summary["updated"] += 1
        return False

    # -- alta manual -------------------------------------------------------

    def create_manual(self, payload: dict):
        content = {
            "rating": payload.get("rating"),
            "text": payload.get("text") or "",
            "language": payload.get("language"),
            "author": payload.get("author") or {},
            "published_at": payload.get("published_at") or datetime.utcnow(),
        }
        status, reason = self._auto_moderate(content)
        doc = {
            "tenant_id": payload["tenant_id"],
            "provider": "manual",
            "external_id": payload.get("external_id") or f"manual-{uuid4().hex}",
            **content,
            "status": status,
            "moderation": {"auto": True, "reason": reason, "by": None, "at": None},
            "is_featured": payload.get("is_featured", False),
            "display_order": payload.get("display_order"),
        }
        if self.repo.get_by_external_id(doc["tenant_id"], "manual", doc["external_id"]):
            return {"conflict": "review with this external_id already exists"}
        _id = self.repo.insert(doc)
        return self.repo.get(_id)

    # -- lectura y edición -------------------------------------------------

    def get(self, review_id: str):
        return self.repo.get(review_id)

    def list(self, query_args: dict):
        filters: dict = {}
        for key in ("tenant_id", "provider", "status"):
            value = query_args.get(key)
            if value:
                filters[key] = value
        rating = query_args.get("rating")
        if rating is not None:
            filters["rating"] = rating
        skip = query_args.get("skip", 0)
        limit = query_args.get("limit", 20)
        return {
            "items": self.repo.list(filters, skip=skip, limit=limit),
            "total": self.repo.count(filters),
            "skip": skip,
            "limit": limit,
        }

    def update(self, review_id: str, payload: dict):
        """Solo edita presentación. El contenido lo manda el origen y `status`
        tiene su propio endpoint (`/moderate`)."""
        r = self.repo.get(review_id)
        if not r:
            return None
        allowed = ("is_featured", "display_order")
        patch = {k: v for k, v in payload.items() if k in allowed}
        if not patch:
            return r
        return self.repo.update(review_id, patch)

    def moderate(self, review_id: str, status: str, user_id: Optional[str] = None):
        if status not in VALID_STATUSES:
            return {"error": f"invalid status, expected one of {list(VALID_STATUSES)}"}
        r = self.repo.get(review_id)
        if not r:
            return None
        return self.repo.update(
            review_id,
            {
                "status": status,
                "moderation": {
                    "auto": False,  # marca la decisión humana: el sync ya no la pisa
                    "reason": "manual moderation",
                    "by": user_id,
                    "at": datetime.utcnow(),
                },
            },
        )

    def delete(self, review_id: str):
        r = self.repo.get(review_id)
        if not r:
            return None
        self.repo.delete(review_id)
        return {"ok": True}

    # -- listado público ---------------------------------------------------

    def public_list(self, tenant_id: Optional[str] = None, limit: Optional[int] = None):
        """Reseñas aprobadas para la landing, con media y total."""
        items = sorted(self.repo.find_public(tenant_id=tenant_id), key=self._public_sort_key)
        total = len(items)
        ratings = [r.get("rating") for r in items if isinstance(r.get("rating"), int)]
        average = round(sum(ratings) / len(ratings), 2) if ratings else None
        if limit:
            items = items[:limit]
        return {
            "items": [self._to_public(r) for r in items],
            "total": total,
            "average_rating": average,
        }

    @staticmethod
    def _public_sort_key(r: dict):
        """Orden del listado público, en cascada:

        1. `display_order` ascendente (menor = más arriba).
        2. Las que no tienen `display_order` van **al final**, no al principio.
        3. Empates → `published_at` descendente (la más reciente primero).

        Se ordena en Python y no en Mongo a propósito: un `sort` ascendente en
        Mongo pone los `null` primero, justo lo contrario de lo que queremos.
        """
        order = r.get("display_order")
        published = r.get("published_at")
        ts = published.timestamp() if isinstance(published, datetime) else 0
        return (order is None, order if order is not None else 0, -ts)

    @staticmethod
    def _to_public(r: dict):
        author = r.get("author") or {}
        return {
            "rating": r.get("rating"),
            "text": r.get("text"),
            "author_name": author.get("name"),
            "author_photo_url": author.get("photo_url"),
            "author_profile_url": author.get("profile_url"),
            "published_at": r.get("published_at"),
            "is_featured": r.get("is_featured", False),
        }

    # -- moderación automática --------------------------------------------

    def _auto_moderate(self, content: dict) -> tuple[str, str]:
        """Clasifica una reseña recién llegada.

        - **Sin texto → `rejected`.** En Google ~44% de las reseñas son solo estrellas
          y no tienen nada que pintar en una tarjeta. Mandarlas a `pending` llenaría la
          bandeja de moderación de items que nadie va a poder publicar nunca. Se
          rechazan solas, pero siguen en la base de datos y son recuperables.
        - **Con texto pero por debajo del umbral → `pending`.** Aquí sí hace falta que
          alguien decida: es una crítica real que quizá se quiera publicar (o no).
        - **Con texto y suficientes estrellas → `approved`.**
        """
        rating = content.get("rating")
        if not isinstance(rating, int):
            return STATUS_PENDING, "missing rating"
        if not (content.get("text") or "").strip():
            return STATUS_REJECTED, "empty text: nothing to display"
        if rating < self.min_rating:
            return STATUS_PENDING, f"rating below threshold ({rating} < {self.min_rating})"
        return STATUS_APPROVED, f"rating >= {self.min_rating}"
