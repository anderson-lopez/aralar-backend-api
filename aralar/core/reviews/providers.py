"""Providers de reseñas de Google (patrón Strategy, igual que `core/i18n/providers.py`).

Se selecciona con la env var `GOOGLE_REVIEWS_PROVIDER`:

- ``manual``  → no trae nada de la red; las reseñas se dan de alta por
  ``POST /api/google-reviews/manual``. Es el **default** y no necesita configuración.
- ``scraper`` → consume el endpoint interno de Google Maps (``GetLocalBoqProxy``) con
  peticiones HTTP planas: sin navegador, sin scroll y sin CAPTCHA de por medio.

El endpoint y el mapa de índices de la respuesta están **verificados contra el local
real** (Restaurante Aralar, Bilbao) el 2026-07-26. El endpoint antiguo ``listugcposts``
responde 403 y ya no sirve.

Ninguna función de este módulo lanza excepciones crudas al llamador: los fallos de red
o de formato se envuelven en `ReviewsProviderError` para que el sync los reporte sin
tumbar el proceso ni pisar los datos que ya hay en Mongo.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)


class ReviewsProviderError(RuntimeError):
    """Fallo controlado del provider (red, HTTP, formato ilegible)."""


class ReviewsProvider:
    """Interfaz común. `fetch_reviews` devuelve reseñas ya **normalizadas**."""

    name = "base"

    def fetch_reviews(self, *, tenant_id: str) -> list[dict]:
        raise NotImplementedError


class ManualProvider(ReviewsProvider):
    """Sin origen remoto: las reseñas se cargan a mano desde el panel."""

    name = "manual"

    def fetch_reviews(self, *, tenant_id: str) -> list[dict]:
        return []


# ---------------------------------------------------------------------------
# Scraper del endpoint interno de Google Maps
# ---------------------------------------------------------------------------

# Prefijo anti-JSON-hijacking que Google antepone a la respuesta.
_ANTI_HIJACK_PREFIX = ")]}'"

# `feature_id` de un local: par de enteros hex que aparece en la URL de Maps
# como `!1s0x1234abcd:0x5678ef90` o como `data=...:0x...`.
_FEATURE_ID_RE = re.compile(r"(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)")

# Señales de alta confianza usadas por el parseo tolerante (ver `_parse_review`).
_PHOTO_URL_RE = re.compile(r"^https?://lh\d+\.googleusercontent\.com/", re.IGNORECASE)
_PROFILE_URL_RE = re.compile(r"^https?://www\.google\.com/maps/contrib/", re.IGNORECASE)

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def _dig(node, *path, default=None):
    """Acceso tolerante a estructuras anidadas de listas/dicts.

    La respuesta de Google es *protobuf serializado como arrays indexados por
    posición*, así que cualquier acceso directo (``node[0][2][15]``) revienta con
    `IndexError`/`TypeError` en cuanto Google reordena un nivel. Este helper
    devuelve `default` en vez de propagar.
    """
    cur = node
    for key in path:
        try:
            cur = cur[key]
        except (IndexError, KeyError, TypeError):
            return default
    if cur is None:
        return default
    return cur


def _walk(node, depth=0, max_depth=12):
    """Recorre en profundidad la estructura anidada devolviendo cada valor escalar."""
    if depth > max_depth:
        return
    if isinstance(node, (list, tuple)):
        for item in node:
            yield from _walk(item, depth + 1, max_depth)
    elif isinstance(node, dict):
        for item in node.values():
            yield from _walk(item, depth + 1, max_depth)
    else:
        yield node


def _epoch_to_datetime(value):
    """Convierte el timestamp de Google a `datetime` UTC.

    Google devuelve los milisegundos **como cadena** (``"1760522012804"``) y en otros
    campos usa micro o nanosegundos, así que se acepta str/int/float y se normaliza
    por magnitud en vez de asumir una unidad fija.
    """
    if isinstance(value, str):
        value = value.strip()
        if not value.isdigit():
            return None
        value = int(value)
    if not isinstance(value, (int, float)) or value <= 0:
        return None
    v = float(value)
    if v > 1e17:      # nanosegundos
        v /= 1e9
    elif v > 1e14:    # microsegundos
        v /= 1e6
    elif v > 1e11:    # milisegundos
        v /= 1e3
    try:
        return datetime.fromtimestamp(v, tz=timezone.utc).replace(tzinfo=None)
    except (OverflowError, OSError, ValueError):
        return None


class GoogleMapsScraperProvider(ReviewsProvider):
    """Lee las reseñas públicas de un local vía el endpoint interno de Maps.

    No usa navegador: es un `GET` paginado con token. El punto frágil es el
    **mapa de índices** de la respuesta, que vive íntegro en `_parse_review` para
    que un cambio de formato se arregle en un único sitio.
    """

    name = "scraper"

    ENDPOINT = (
        "https://www.google.com/httpservice/web/PrivateLocalSearchUiDataService/GetLocalBoqProxy"
    )
    PAGE_SIZE = 10

    # Orden de las reseñas: 1 relevantes · 2 recientes · 3 mejor valoradas · 4 peores.
    # Por defecto las más recientes: el sync es incremental y así lo nuevo entra primero.
    SORT_NEWEST = 2

    def __init__(
        self,
        *,
        feature_id: str = "",
        place_url: str = "",
        locale: str = "es",
        max_pages: int = 10,
        timeout: int = 20,
        user_agent: str = _DEFAULT_USER_AGENT,
        pause_seconds: float = 1.0,
        sort_order: int = SORT_NEWEST,
    ):
        self.feature_id = feature_id or self.extract_feature_id(place_url)
        self.locale = locale or "es"
        self.max_pages = max(1, int(max_pages))
        self.timeout = timeout
        self.user_agent = user_agent or _DEFAULT_USER_AGENT
        self.pause_seconds = pause_seconds
        self.sort_order = int(sort_order)

    # -- entrada pública ---------------------------------------------------

    def fetch_reviews(self, *, tenant_id: str) -> list[dict]:
        if not self.feature_id:
            raise ReviewsProviderError(
                "missing feature id: set GOOGLE_MAPS_FEATURE_ID or GOOGLE_MAPS_PLACE_URL"
            )

        reviews: list[dict] = []
        seen: set[str] = set()
        token = ""

        for _ in range(self.max_pages):
            payload = self._request_page(token)
            page_reviews, token = self._parse_page(payload)

            new_in_page = 0
            for item in page_reviews:
                ext_id = item.get("external_id")
                if not ext_id or ext_id in seen:
                    continue
                seen.add(ext_id)
                reviews.append(item)
                new_in_page += 1

            # Sin token o sin elementos nuevos: no hay más que traer.
            if not token or new_in_page == 0:
                break
            if self.pause_seconds:
                time.sleep(self.pause_seconds)

        return reviews

    @staticmethod
    def extract_feature_id(place_url: str) -> str:
        """Saca el `feature_id` (``0x...:0x...``) de una URL de Google Maps."""
        if not place_url:
            return ""
        match = _FEATURE_ID_RE.search(place_url)
        return match.group(1) if match else ""

    # -- red ---------------------------------------------------------------

    def _request_page(self, token: str) -> str:
        params = {"msc": "gwsrpc", "reqpld": self._build_payload(token)}
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "*/*",
            "Accept-Language": f"{self.locale}-ES,{self.locale};q=0.9",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Referer": "https://www.google.com/maps/",
        }
        try:
            resp = requests.get(
                self.ENDPOINT, params=params, headers=headers, timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise ReviewsProviderError(f"request to Google Maps failed: {exc}") from exc

        if resp.status_code == 429:
            raise ReviewsProviderError("rate limited by Google (HTTP 429)")
        if resp.status_code != 200:
            raise ReviewsProviderError(f"unexpected HTTP status {resp.status_code}")
        return resp.text

    def _build_payload(self, token: str) -> str:
        """Construye el `reqpld`: un JSON anidado con el local, el orden y la página.

        La forma cambia entre la primera página y las siguientes: en la primera va el
        tamaño de página en la posición 9, y en las demás va el token de paginación en
        la 19. Es la misma petición que emite la web de Maps al abrir las reseñas.
        """
        if token:
            inner = [
                None, self.sort_order, None, None, None, None, None, None, None,
                None, None, [self.feature_id], None, None, None, None, None, None,
                None, token,
            ]
        else:
            inner = [
                None, self.sort_order, None, None, None, None, None, None, None,
                self.PAGE_SIZE, None, [self.feature_id],
            ]
        payload = [None, [None, None, None, None, None, None, None, None, None, inner]]
        return json.dumps(payload, separators=(",", ":"))

    # -- parseo ------------------------------------------------------------

    @staticmethod
    def _load_payload(text: str):
        """Quita el prefijo anti-hijacking y decodifica el JSON."""
        if not text:
            raise ReviewsProviderError("empty response from Google")
        cleaned = text.split(_ANTI_HIJACK_PREFIX, 1)[-1].lstrip()
        try:
            return json.loads(cleaned)
        except (ValueError, TypeError) as exc:
            raise ReviewsProviderError(f"could not decode Google response: {exc}") from exc

    def _parse_page(self, text: str) -> tuple[list[dict], str]:
        """Devuelve `(reseñas, token_siguiente)` de una página."""
        data = self._load_payload(text)

        # Layout verificado contra el endpoint real:
        #   data[1][10][2] → lista de reseñas
        #   data[1][10][6] → token de la página siguiente
        container = _dig(data, 1, 10, default=None)
        raw_reviews = _dig(container, 2, default=None)
        if not isinstance(raw_reviews, list):
            raw_reviews = self._find_review_nodes(data)

        next_token = _dig(container, 6, default="") or ""
        if not isinstance(next_token, str):
            next_token = ""

        parsed: list[dict] = []
        for node in raw_reviews or []:
            try:
                item = self._parse_review(node)
            except Exception:  # noqa: BLE001 - una reseña rota no aborta el lote
                logger.warning("google_reviews: review node could not be parsed", exc_info=True)
                continue
            if item:
                parsed.append(item)

        return parsed, next_token

    @staticmethod
    def _find_review_nodes(data):
        """Fallback: localiza la lista de reseñas si no está en el índice esperado.

        Busca la lista más larga cuyos elementos parezcan nodos de reseña (una
        lista con un id de texto en la posición 5 y una valoración en la 1).
        """
        best: list = []

        def looks_like_review(x):
            return (
                isinstance(x, list)
                and len(x) > 5
                and isinstance(_dig(x, 5), str)
                and isinstance(_dig(x, 1), int)
            )

        def visit(node, depth=0):
            nonlocal best
            if depth > 8 or not isinstance(node, list):
                return
            if node and len(node) > len(best) and all(looks_like_review(x) for x in node):
                best = node
            for item in node:
                visit(item, depth + 1)

        visit(data)
        return best

    @classmethod
    def _parse_review(cls, node) -> dict | None:
        """Mapea un nodo crudo a la forma normalizada.

        ⚠️ **Único punto acoplado al formato de Google.** Mapa verificado contra la
        respuesta real (2026-07-26):

        =========================  ==========================================
        ``r[1]``                   valoración 1-5
        ``r[2][0]`` / ``r[2][2]``  fecha relativa / epoch en **ms como cadena**
        ``r[3][0..2]``             autor: nombre, foto, perfil
        ``r[5]``                   id estable de la reseña
        ``r[26]``                  idioma
        ``r[27]``                  texto completo (``r[28]`` es un preview truncado)
        =========================  ==========================================

        Si un campo no aparece donde se espera, se cae a una búsqueda por señal
        dentro del propio nodo (URL de avatar, entero 1-5, epoch). Así un
        reordenamiento parcial degrada el dato pero no rompe la extracción.
        """
        if not isinstance(node, (list, tuple)) or not node:
            return None

        external_id = _dig(node, 5)
        if not isinstance(external_id, str) or not external_id:
            return None

        author_block = _dig(node, 3, default=None)
        author_name = _dig(author_block, 0)
        photo_url = _dig(author_block, 1)
        profile_url = _dig(author_block, 2)

        rating = _dig(node, 1)
        # r[27] es el texto íntegro; r[28] viene recortado para el preview de la ficha.
        text = _dig(node, 27) or _dig(node, 28)
        language = _dig(node, 26)
        published_raw = _dig(node, 2, 2)

        scalars = None  # se calcula perezosamente: recorrer el nodo no es gratis

        def signals():
            nonlocal scalars
            if scalars is None:
                scalars = list(_walk(node))
            return scalars

        if not isinstance(photo_url, str) or not _PHOTO_URL_RE.match(photo_url or ""):
            photo_url = next(
                (s for s in signals() if isinstance(s, str) and _PHOTO_URL_RE.match(s)), None
            )
        if not isinstance(profile_url, str) or not _PROFILE_URL_RE.match(profile_url or ""):
            profile_url = next(
                (s for s in signals() if isinstance(s, str) and _PROFILE_URL_RE.match(s)), None
            )
        if not isinstance(rating, int) or not 1 <= rating <= 5:
            rating = next(
                (s for s in signals() if isinstance(s, int) and 1 <= s <= 5), None
            )
        if not isinstance(text, str):
            text = ""

        published_at = _epoch_to_datetime(published_raw)
        if published_at is None:
            published_at = next(
                (
                    dt
                    for dt in (
                        _epoch_to_datetime(s)
                        for s in signals()
                        if isinstance(s, (int, float)) and s > 1e11
                    )
                    if dt is not None
                ),
                None,
            )

        if rating is None:
            return None

        return {
            "external_id": external_id,
            "rating": int(rating),
            "text": (text or "").strip(),
            "language": language if isinstance(language, str) else None,
            "author": {
                "name": author_name if isinstance(author_name, str) else None,
                "photo_url": photo_url,
                "profile_url": profile_url,
            },
            "published_at": published_at,
            "raw": None,
        }


def get_provider(config) -> ReviewsProvider:
    """Devuelve el provider según `GOOGLE_REVIEWS_PROVIDER` (default `manual`)."""
    name = (config.get("GOOGLE_REVIEWS_PROVIDER") or "manual").lower()
    if name == "scraper":
        return GoogleMapsScraperProvider(
            feature_id=config.get("GOOGLE_MAPS_FEATURE_ID", ""),
            place_url=config.get("GOOGLE_MAPS_PLACE_URL", ""),
            locale=config.get("GOOGLE_REVIEWS_LOCALE", "es"),
            max_pages=config.get("GOOGLE_REVIEWS_MAX_PAGES", 10),
            timeout=config.get("GOOGLE_REVIEWS_TIMEOUT", 20),
            user_agent=config.get("GOOGLE_REVIEWS_USER_AGENT", _DEFAULT_USER_AGENT),
        )
    return ManualProvider()
