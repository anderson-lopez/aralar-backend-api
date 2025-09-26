import requests
import re


class I18nProvider:
    def translate(
        self, src: str | None, tgt: str, texts: list[str], glossary=None
    ) -> tuple[str, list[str]]:
        raise NotImplementedError

    def detect(self, texts: list[str]) -> list[str]:
        raise NotImplementedError


# ---- DeepL ----
class DeepLProvider(I18nProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.deepl.com/v2"):
        self.key = api_key
        self.base = base_url.rstrip("/")

    def apply_local_glossary(self, texts, glossary):
        """Aplica glosario local ANTES de enviar a DeepL"""
        if not glossary or not glossary.get("pairs"):
            return texts

        processed_texts = []
        for text in texts:
            processed_text = text
            # Aplicar cada par del glosario
            for pair in glossary["pairs"]:
                for source_term, target_term in pair.items():
                    # Reemplazar términos completos (no parciales)
                    pattern = r"\b" + re.escape(source_term) + r"\b"
                    processed_text = re.sub(
                        pattern, target_term, processed_text, flags=re.IGNORECASE
                    )
            processed_texts.append(processed_text)

        return processed_texts

    def restore_glossary_terms(self, translated_texts, original_texts, glossary):
        """Asegura que los términos del glosario se mantuvieron en la traducción"""
        if not glossary or not glossary.get("pairs"):
            return translated_texts

        restored_texts = []
        for i, translated in enumerate(translated_texts):
            restored_text = translated
            # Verificar que los términos del glosario se mantuvieron
            for pair in glossary["pairs"]:
                for source_term, target_term in pair.items():
                    # Si el término original contenía un término del glosario
                    if re.search(
                        r"\b" + re.escape(source_term) + r"\b", original_texts[i], re.IGNORECASE
                    ):
                        # Asegurar que el término traducido esté en el resultado
                        if target_term.lower() not in restored_text.lower():
                            # Si DeepL no respetó nuestro glosario, forzar el reemplazo
                            pattern = r"\b" + re.escape(source_term) + r"\b"
                            restored_text = re.sub(
                                pattern, target_term, restored_text, flags=re.IGNORECASE
                            )
            restored_texts.append(restored_text)

        return restored_texts

    def translate(self, src, tgt, texts, glossary=None):
        # 1. Aplicar glosario local ANTES de enviar a DeepL
        processed_texts = self.apply_local_glossary(texts, glossary)

        # 2. Preparar datos para DeepL
        data = {
            "target_lang": tgt,
        }
        if src:
            data["source_lang"] = src
        for t in processed_texts:
            data.setdefault("text", []).append(t)

        # 3. Glosario de DeepL (si existe)
        if glossary and glossary.get("deepl_glossary_id"):
            data["glossary_id"] = glossary["deepl_glossary_id"]

        # 4. Llamar a DeepL
        r = requests.post(
            f"{self.base}/translate",
            data=data,
            headers={"Authorization": f"DeepL-Auth-Key {self.key}"},
        )
        r.raise_for_status()
        js = r.json()
        translated_texts = [x["text"] for x in js.get("translations", [])]

        # 5. Restaurar términos del glosario si DeepL los cambió
        final_texts = self.restore_glossary_terms(translated_texts, texts, glossary)

        src_out = js.get("translations", [{}])[0].get("detected_source_language", src or "")
        return src_out, final_texts

    def detect(self, texts):
        # DeepL no tiene “detect” dedicado; podemos traducir a mismo idioma o usar heurística simple.
        # Alternativa: usar el primer resultado de translate sin target (o usa Google para detect si mezclas drivers).
        # Como placeholder, devolvemos "auto".
        return ["auto"] * len(texts)


# ---- Google Translate v2 ----
class GoogleProvider(I18nProvider):
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://translation.googleapis.com/language/translate/v2",
    ):
        self.key = api_key
        self.base = base_url.rstrip("/")

    def apply_local_glossary(self, texts, glossary):
        """Aplica glosario local ANTES de enviar a Google Translate"""
        if not glossary or not glossary.get("pairs"):
            return texts

        processed_texts = []
        for text in texts:
            processed_text = text
            # Aplicar cada par del glosario
            for pair in glossary["pairs"]:
                for source_term, target_term in pair.items():
                    # Reemplazar términos completos (no parciales)
                    pattern = r"\b" + re.escape(source_term) + r"\b"
                    processed_text = re.sub(
                        pattern, target_term, processed_text, flags=re.IGNORECASE
                    )
            processed_texts.append(processed_text)

        return processed_texts

    def restore_glossary_terms(self, translated_texts, original_texts, glossary):
        """Asegura que los términos del glosario se mantuvieron en la traducción"""
        if not glossary or not glossary.get("pairs"):
            return translated_texts

        restored_texts = []
        for i, translated in enumerate(translated_texts):
            restored_text = translated
            # Verificar que los términos del glosario se mantuvieron
            for pair in glossary["pairs"]:
                for source_term, target_term in pair.items():
                    # Si el término original contenía un término del glosario
                    if re.search(
                        r"\b" + re.escape(source_term) + r"\b", original_texts[i], re.IGNORECASE
                    ):
                        # Asegurar que el término traducido esté en el resultado
                        if target_term.lower() not in restored_text.lower():
                            # Si Google no respetó nuestro glosario, forzar el reemplazo
                            pattern = r"\b" + re.escape(source_term) + r"\b"
                            restored_text = re.sub(
                                pattern, target_term, restored_text, flags=re.IGNORECASE
                            )
            restored_texts.append(restored_text)

        return restored_texts

    def translate(self, src, tgt, texts, glossary=None):
        # 1. Aplicar glosario local ANTES de enviar a Google
        processed_texts = self.apply_local_glossary(texts, glossary)

        # 2. Preparar datos para Google Translate
        data = {
            "q": processed_texts,
            "target": tgt,
        }
        if src and src != "auto":
            data["source"] = src

        # 3. Llamar a Google Translate API
        headers = {"Content-Type": "application/json; charset=utf-8"}

        # Usar API key en la URL (método más simple)
        url = f"{self.base}?key={self.key}"

        r = requests.post(url, json=data, headers=headers)
        print(url)
        print("peticion google")
        r.raise_for_status()
        js = r.json()

        # 4. Procesar respuesta
        translations = js.get("data", {}).get("translations", [])
        translated_texts = [t["translatedText"] for t in translations]

        # 5. Restaurar términos del glosario si Google los cambió
        final_texts = self.restore_glossary_terms(translated_texts, texts, glossary)

        # 6. Detectar idioma fuente si no se especificó
        detected_lang = src or "auto"
        if translations and "detectedSourceLanguage" in translations[0]:
            detected_lang = translations[0]["detectedSourceLanguage"]

        return detected_lang, final_texts

    def detect(self, texts):
        """Detecta el idioma de los textos usando Google Translate API"""
        if not texts:
            return []

        # Google Translate detect endpoint
        data = {"q": texts}
        headers = {"Content-Type": "application/json; charset=utf-8"}
        url = f"{self.base}/detect?key={self.key}"

        try:
            r = requests.post(url, json=data, headers=headers)
            r.raise_for_status()
            js = r.json()

            # Procesar respuesta de detección
            detections = js.get("data", {}).get("detections", [])
            detected_langs = []

            for detection_group in detections:
                if detection_group and len(detection_group) > 0:
                    # Tomar la primera detección (más confiable)
                    detected_langs.append(detection_group[0].get("language", "auto"))
                else:
                    detected_langs.append("auto")

            return detected_langs

        except Exception:
            # Fallback si falla la detección
            return ["auto"] * len(texts)


def get_provider(config):
    p = (config.get("I18N_PROVIDER") or "deepl").lower()

    if p == "deepl":
        api_key = config.get("DEEPL_API_KEY", "")
        base_url = config.get("DEEPL_BASE_URL", "https://api.deepl.com/v2")
        return DeepLProvider(api_key, base_url)

    if p == "google":
        api_key = config.get("GOOGLE_API_KEY", "")
        base_url = config.get(
            "GOOGLE_BASE_URL", "https://translation.googleapis.com/language/translate/v2"
        )
        return GoogleProvider(api_key, base_url)

    # Default fallback
    api_key = config.get("DEEPL_API_KEY", "")
    base_url = config.get("DEEPL_BASE_URL", "https://api.deepl.com/v2")
    return DeepLProvider(api_key, base_url)
