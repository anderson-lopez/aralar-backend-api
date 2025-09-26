from ..repositories.translations_repo import TranslationsRepo


class I18nService:
    def __init__(self, db, provider, provider_name: str):
        self.provider = provider
        self.provider_name = (provider_name or "deepl").lower()
        self.cache = TranslationsRepo(db)

    def translate_batch(
        self, tenant_id: str, texts: list[str], src: str | None, tgt: str, glossary: dict | None
    ):
        if not texts:
            return {"items": []}

        glossary_version = (glossary or {}).get("version")
        provider_name = self.provider_name

        # 1) cache lookup
        items = []
        to_query = []
        positions = []
        for i, t in enumerate(texts):
            h = self.cache.make_hash(
                t.strip(), (src or "auto").lower(), tgt.lower(), provider_name, glossary_version
            )
            cached = self.cache.get(h)
            if cached:
                items.append({"source": t, "translated": cached["translated_text"], "cached": True})
            else:
                items.append(None)
                to_query.append(t)
                positions.append(i)

        # 2) provider call for misses
        if to_query:
            src_detected, translated = self.provider.translate(
                src, tgt, to_query, glossary=glossary
            )
            for idx, txt in enumerate(translated):
                pos = positions[idx]
                items[pos] = {"source": texts[pos], "translated": txt, "cached": False}
                # put into cache
                h = self.cache.make_hash(
                    texts[pos].strip(),
                    (src or "auto").lower(),
                    tgt.lower(),
                    provider_name,
                    glossary_version,
                )
                self.cache.put(
                    h,
                    {
                        "tenant_id": tenant_id,
                        "source_text": texts[pos],
                        "source_lang": src or src_detected,
                        "target_lang": tgt,
                        "provider": provider_name,
                        "glossary_version": glossary_version,
                        "translated_text": txt,
                    },
                )

        # 3) fill (shouldn’t be any None)
        items = [x for x in items if x is not None]
        return {
            "provider": provider_name,
            "source_lang": src or "auto",
            "target_lang": tgt,
            "items": items,
        }

    def detect(self, texts: list[str]):
        # Podrías usar provider.detect; aquí devolvemos heurística simple o "auto".
        langs = self.provider.detect(texts)
        return {"items": [{"text": t, "lang": l} for t, l in zip(texts, langs)]}
