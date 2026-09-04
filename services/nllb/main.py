import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.config import settings
from src.translator import init_translator
from src.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.environ.setdefault("HF_HOME", settings.hf_home)
    init_translator(
        model_name=settings.model_name,
        device=settings.device,
        src_lang=settings.source_lang,
        target_langs=settings.target_langs_dict,
    )
    yield


app = FastAPI(
    title="NLLB Translation Service",
    description="Translation service using facebook/nllb-200-distilled-600M",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
