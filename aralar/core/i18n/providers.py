import requests


class I18nProvider:
    def translate(
        self, src: str | None, tgt: str, texts: list[str], glossary=None
    ) -> tuple[str, list[str]]:
        raise NotImplementedError

    def detect(self, texts: list[str]) -> list[str]:
        raise NotImplementedError


# ---- DeepL ----
class DeepLProvider(I18nProvider):
    def __init__(self, api_key: str):
        self.key = api_key
        self.base = "https://api.deepl.com/v2"

    def translate(self, src, tgt, texts, glossary=None):
        # DeepL acepta source_lang opcional; target obligatorio
        data = {
            "target_lang": tgt,
        }
        if src:
            data["source_lang"] = src
        for t in texts:
            data.setdefault("text", []).append(t)

        # glossario: con DeepL hay "glossary_id" si lo creaste
        if glossary and glossary.get("deepl_glossary_id"):
            data["glossary_id"] = glossary["deepl_glossary_id"]

        r = requests.post(
            f"{self.base}/translate",
            data=data,
            headers={"Authorization": f"DeepL-Auth-Key {self.key}"},
        )
        r.raise_for_status()
        js = r.json()
        out = [x["text"] for x in js.get("translations", [])]
        src_out = js.get("translations", [{}])[0].get("detected_source_language", src or "")
        return src_out, out

    def detect(self, texts):
        # DeepL no tiene “detect” dedicado; podemos traducir a mismo idioma o usar heurística simple.
        # Alternativa: usar el primer resultado de translate sin target (o usa Google para detect si mezclas drivers).
        # Como placeholder, devolvemos "auto".
        return ["auto"] * len(texts)


# ---- Google v3 (esquema) ----
class GoogleProvider(I18nProvider):
    # Aquí iría el cliente oficial de Google (google-cloud-translate).
    # Omitido por brevedad; la interfase es la misma que la de DeepL.
    pass


def get_provider(config):
    p = (config.get("I18N_PROVIDER") or "deepl").lower()
    if p == "deepl":
        return DeepLProvider(config.get("DEEPL_API_KEY", ""))
    if p == "google":
        return GoogleProvider()
    return DeepLProvider(config.get("DEEPL_API_KEY", ""))
