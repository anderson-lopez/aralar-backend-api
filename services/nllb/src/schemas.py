from pydantic import BaseModel


class TranslationRequest(BaseModel):
    text: str


class TranslateSingleRequest(BaseModel):
    text: str
    target_lang: str
    source_lang: str | None = None


class TranslateBatchRequest(BaseModel):
    texts: list[str]
    target_lang: str
    source_lang: str | None = None


class TranslationResponse(BaseModel):
    source_lang: str
    source_text: str
    target_lang: str
    translated_text: str


class TranslationBatchItem(BaseModel):
    source: str
    translated: str


class TranslationBatchResponse(BaseModel):
    source_lang: str
    target_lang: str
    items: list[TranslationBatchItem]


class LangText(BaseModel):
    lang_name: str
    text: str


class TranslationAllResponse(BaseModel):
    source_lang: str
    source_text: str
    translations: dict[str, LangText]


class HealthResponse(BaseModel):
    status: str
    model: str
    device: str


class LanguageInfo(BaseModel):
    code: str
    name: str


class LanguagesResponse(BaseModel):
    source: LanguageInfo
    targets: list[LanguageInfo]
