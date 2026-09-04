from fastapi import HTTPException

from src.schemas import (
    TranslationRequest,
    TranslateSingleRequest,
    TranslateBatchRequest,
    TranslationResponse,
    TranslationBatchResponse,
    TranslationBatchItem,
    TranslationAllResponse,
    LangText,
    HealthResponse,
    LanguagesResponse,
    LanguageInfo,
)
from src.translator import get_translator
from src.config import settings


def _validate_lang(lang: str, param: str = "target_lang"):
    if lang not in settings.target_langs_dict:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported {param}: '{lang}'. Choose from: {list(settings.target_langs_dict.keys())}",
        )


async def translate_single(request: TranslateSingleRequest):
    _validate_lang(request.target_lang)
    if request.source_lang:
        _validate_lang(request.source_lang, "source_lang")

    translator = get_translator()
    result = translator.translate(request.text, request.target_lang, request.source_lang)

    return TranslationResponse(
        source_lang=request.source_lang or settings.source_lang,
        source_text=request.text,
        target_lang=request.target_lang,
        translated_text=result,
    )


async def translate_batch(request: TranslateBatchRequest):
    _validate_lang(request.target_lang)
    if request.source_lang:
        _validate_lang(request.source_lang, "source_lang")

    if not request.texts:
        raise HTTPException(status_code=400, detail="texts list cannot be empty")
    if len(request.texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts per request")

    translator = get_translator()
    translated = translator.translate_batch(
        request.texts, request.target_lang, request.source_lang
    )

    items = [
        TranslationBatchItem(source=src, translated=tgt)
        for src, tgt in zip(request.texts, translated)
    ]

    return TranslationBatchResponse(
        source_lang=request.source_lang or settings.source_lang,
        target_lang=request.target_lang,
        items=items,
    )


async def translate_all(request: TranslationRequest):
    translator = get_translator()
    raw_results = translator.translate_all(request.text)

    translations = {}
    for code, data in raw_results.items():
        translations[code] = LangText(**data)

    return TranslationAllResponse(
        source_lang=settings.source_lang,
        source_text=request.text,
        translations=translations,
    )


async def health():
    translator = get_translator()
    return HealthResponse(
        status="ok",
        model=settings.model_name,
        device=translator.device,
    )


async def get_languages():
    all_langs = settings.target_langs_dict
    targets = [
        LanguageInfo(code=code, name=info["name"])
        for code, info in all_langs.items()
        if code != settings.source_lang
    ]
    source_info = all_langs.get(settings.source_lang, {"name": settings.source_lang})
    return LanguagesResponse(
        source=LanguageInfo(code=settings.source_lang, name=source_info["name"]),
        targets=targets,
    )
