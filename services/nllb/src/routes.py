from fastapi import APIRouter

from src.schemas import TranslationRequest, TranslateSingleRequest, TranslateBatchRequest
from src.controller import (
    translate_single,
    translate_batch,
    translate_all,
    health as health_handler,
    get_languages,
)

router = APIRouter(prefix="/api/v1")


@router.post("/translate")
async def translate_endpoint(body: TranslateSingleRequest):
    return await translate_single(body)


@router.post("/translate/batch")
async def translate_batch_endpoint(body: TranslateBatchRequest):
    return await translate_batch(body)


@router.post("/translate/all")
async def translate_all_endpoint(body: TranslationRequest):
    return await translate_all(body)


@router.get("/health")
async def health_endpoint():
    return await health_handler()


@router.get("/languages")
async def languages_endpoint():
    return await get_languages()
