"""
Tests del módulo de i18n (proveedores de traducción: DeepL, Google).

Referencias:
- Providers: `aralar/core/i18n/providers.py`
- Service:   `aralar/services/i18n_service.py`
- Blueprint: `aralar/api/i18n/blueprint.py`

⚠️ Los providers hacen llamadas HTTP a APIs externas (DeepL/Google).
Mockeamos `requests.post` para que los tests NO hagan llamadas reales.
"""
from unittest.mock import patch, MagicMock

import pytest

from aralar.core.i18n.providers import (
    get_provider,
    DeepLProvider,
    GoogleProvider,
)


@pytest.mark.unit
class TestGetProvider:
    """Tests de `get_provider(config)`."""

    def test_returns_deepl_provider_when_configured(self):
        provider = get_provider({"I18N_PROVIDER": "deepl", "DEEPL_API_KEY": "key123"})
        assert isinstance(provider, DeepLProvider)

    def test_returns_google_provider_when_configured(self):
        provider = get_provider({"I18N_PROVIDER": "google", "GOOGLE_API_KEY": "key123"})
        assert isinstance(provider, GoogleProvider)

    def test_falls_back_to_deepl_when_unknown_provider(self):
        provider = get_provider({"I18N_PROVIDER": "unknown"})
        assert isinstance(provider, DeepLProvider)

    def test_uses_default_deepl_base_url_when_not_set(self):
        provider = get_provider({"I18N_PROVIDER": "deepl", "DEEPL_API_KEY": "x"})
        assert provider.base == "https://api.deepl.com/v2"

    def test_uses_custom_base_url_when_provided(self):
        provider = get_provider({
            "I18N_PROVIDER": "deepl",
            "DEEPL_API_KEY": "x",
            "DEEPL_BASE_URL": "https://my-deepl.local/v2",
        })
        assert provider.base == "https://my-deepl.local/v2"


@pytest.mark.unit
class TestDeepLProvider:
    """Tests del DeepLProvider (con `requests.post` mockeado)."""

    def test_translate_returns_text_from_deepl_response(self):
        provider = DeepLProvider(api_key="fake")
        fake_resp = MagicMock()
        fake_resp.json.return_value = {
            "translations": [{"text": "Hello", "detected_source_language": "ES"}]
        }
        fake_resp.raise_for_status.return_value = None
        with patch("aralar.core.i18n.providers.requests.post", return_value=fake_resp):
            src, translated = provider.translate("es", "en", ["Hola"])
        assert translated == ["Hello"]

    def test_translate_sends_authorization_header_with_api_key(self):
        provider = DeepLProvider(api_key="MY-KEY")
        fake_resp = MagicMock()
        fake_resp.json.return_value = {"translations": [{"text": "x"}]}
        fake_resp.raise_for_status.return_value = None
        with patch(
            "aralar.core.i18n.providers.requests.post", return_value=fake_resp
        ) as mock_post:
            provider.translate("es", "en", ["Hola"])
        # Header tiene el API key.
        sent_headers = mock_post.call_args.kwargs["headers"]
        assert "DeepL-Auth-Key MY-KEY" == sent_headers["Authorization"]

    def test_translate_raises_on_4xx_response(self):
        provider = DeepLProvider(api_key="x")
        import requests
        fake_resp = MagicMock()
        fake_resp.raise_for_status.side_effect = requests.HTTPError("400 bad")
        with patch("aralar.core.i18n.providers.requests.post", return_value=fake_resp):
            with pytest.raises(requests.HTTPError):
                provider.translate("es", "en", ["Hola"])

    def test_apply_local_glossary_replaces_terms_case_insensitively(self):
        provider = DeepLProvider(api_key="x")
        glossary = {"pairs": [{"vino": "wine"}]}
        result = provider.apply_local_glossary(["Vino tinto", "VINO blanco"], glossary)
        assert result == ["wine tinto", "wine blanco"]

    def test_detect_returns_auto_placeholder(self):
        provider = DeepLProvider(api_key="x")
        assert provider.detect(["a", "b"]) == ["auto", "auto"]


@pytest.mark.unit
class TestGoogleProvider:
    """Tests del GoogleProvider (con `requests.post` mockeado)."""

    def test_translate_returns_text_from_google_response(self):
        provider = GoogleProvider(api_key="key")
        fake_resp = MagicMock()
        fake_resp.json.return_value = {
            "data": {"translations": [{"translatedText": "Hello",
                                        "detectedSourceLanguage": "es"}]}
        }
        fake_resp.raise_for_status.return_value = None
        with patch("aralar.core.i18n.providers.requests.post", return_value=fake_resp):
            src, translated = provider.translate("es", "en", ["Hola"])
        assert translated == ["Hello"]
        assert src == "es"

    def test_translate_sends_api_key_as_query_param(self):
        provider = GoogleProvider(api_key="GOOGLE-KEY")
        fake_resp = MagicMock()
        fake_resp.json.return_value = {"data": {"translations": [{"translatedText": "x"}]}}
        fake_resp.raise_for_status.return_value = None
        with patch(
            "aralar.core.i18n.providers.requests.post", return_value=fake_resp
        ) as mock_post:
            provider.translate("es", "en", ["Hola"])
        # La URL debe contener el API key.
        url = mock_post.call_args.args[0]
        assert "key=GOOGLE-KEY" in url

    def test_translate_raises_on_4xx_response(self):
        provider = GoogleProvider(api_key="x")
        import requests
        fake_resp = MagicMock()
        fake_resp.raise_for_status.side_effect = requests.HTTPError("400 bad")
        with patch("aralar.core.i18n.providers.requests.post", return_value=fake_resp):
            with pytest.raises(requests.HTTPError):
                provider.translate("es", "en", ["Hola"])

    def test_detect_returns_languages_from_google_response(self):
        provider = GoogleProvider(api_key="x")
        fake_resp = MagicMock()
        fake_resp.json.return_value = {
            "data": {"detections": [[{"language": "es"}], [{"language": "fr"}]]}
        }
        fake_resp.raise_for_status.return_value = None
        with patch("aralar.core.i18n.providers.requests.post", return_value=fake_resp):
            assert provider.detect(["Hola", "Bonjour"]) == ["es", "fr"]

    def test_detect_returns_auto_when_call_fails(self):
        provider = GoogleProvider(api_key="x")
        with patch(
            "aralar.core.i18n.providers.requests.post", side_effect=Exception("net err")
        ):
            assert provider.detect(["a", "b"]) == ["auto", "auto"]


@pytest.mark.integration
class TestI18nService:
    """
    Tests del `I18nService` (cache + provider). Mockeamos el provider para
    no hacer llamadas externas reales.
    """

    def _svc(self, db, provider_mock):
        from aralar.services.i18n_service import I18nService
        return I18nService(db, provider_mock, "deepl")

    def test_returns_empty_items_when_no_texts(self, db):
        provider = MagicMock()
        svc = self._svc(db, provider)
        result = svc.translate_batch(
            tenant_id="aralar", texts=[], src="es", tgt="en", glossary=None
        )
        assert result == {"items": []}
        provider.translate.assert_not_called()

    def test_calls_provider_when_no_cached_translation(self, db):
        provider = MagicMock()
        provider.translate.return_value = ("es", ["Hello"])
        svc = self._svc(db, provider)
        result = svc.translate_batch(
            tenant_id="aralar", texts=["Hola"], src="es", tgt="en", glossary=None
        )
        provider.translate.assert_called_once()
        assert result["items"][0]["translated"] == "Hello"
        assert result["items"][0]["cached"] is False

    def test_returns_cached_translation_without_calling_provider(self, db):
        provider = MagicMock()
        provider.translate.return_value = ("es", ["Hello"])
        svc = self._svc(db, provider)
        # 1ª llamada cachea.
        svc.translate_batch(
            tenant_id="aralar", texts=["Hola"], src="es", tgt="en", glossary=None
        )
        # 2ª llamada con el mismo texto: no debería llamar al provider.
        provider.translate.reset_mock()
        result = svc.translate_batch(
            tenant_id="aralar", texts=["Hola"], src="es", tgt="en", glossary=None
        )
        provider.translate.assert_not_called()
        assert result["items"][0]["cached"] is True

    def test_detect_returns_lang_per_text(self, db):
        provider = MagicMock()
        provider.detect.return_value = ["es", "fr"]
        svc = self._svc(db, provider)
        result = svc.detect(["Hola", "Bonjour"])
        assert result["items"] == [
            {"text": "Hola", "lang": "es"},
            {"text": "Bonjour", "lang": "fr"},
        ]
