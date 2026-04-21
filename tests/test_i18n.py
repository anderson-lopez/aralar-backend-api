"""
Tests del módulo de i18n (proveedores de traducción: DeepL, Google).

Referencias:
- Providers: `aralar/core/i18n/providers.py`
- Service:   `aralar/services/i18n_service.py`
- Blueprint: `aralar/api/i18n/blueprint.py`

⚠️ Los providers hacen llamadas HTTP a APIs externas (DeepL/Google).
Hay que MOCKEAR `requests` para que los tests NO hagan llamadas reales.

Nota: el archivo viejo `test_providers.py` en la raíz del repo ya no se
necesita — su contenido era un script manual con prints, no tests de pytest.
Los reemplazamos por tests proper aquí. Puedes borrarlo cuando cierres este PR.
"""
import pytest


@pytest.mark.unit
class TestGetProvider:
    """
    TODO (junior):
    - test_returns_deepl_provider_when_configured
    - test_returns_google_provider_when_configured
    - test_raises_when_unknown_provider_name
    - test_uses_default_base_url_when_not_configured
    - test_uses_custom_base_url_when_provided
    """
    pass


@pytest.mark.unit
class TestDeepLProvider:
    """
    Mockear `requests.post` para evitar llamadas reales a DeepL.

    TODO (junior):
    - test_translate_returns_text_from_deepl_response
    - test_translate_sends_correct_headers_with_api_key
    - test_translate_raises_on_4xx_response
    - test_translate_handles_empty_text
    """
    pass


@pytest.mark.unit
class TestGoogleProvider:
    """
    TODO (junior):
    - test_translate_returns_text_from_google_response
    - test_translate_sends_api_key_as_query_param
    - test_translate_raises_on_4xx_response
    """
    pass


@pytest.mark.e2e
class TestI18nEndpoints:
    """
    POST /api/i18n/translate

    TODO (junior):
    - test_returns_401_without_token
    - test_returns_translated_text (con provider mockeado)
    - test_returns_400_when_target_locale_unsupported
    """
    pass
