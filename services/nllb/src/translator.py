import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

_translator = None


class Translator:
    def __init__(self, model_name: str, device: str, src_lang: str, target_langs: dict):
        self.device = device if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang=src_lang)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        self.src_lang = src_lang
        self.target_langs = target_langs
        self.lang_codes = list(target_langs.keys())
        self.lang_name_map = {code: info["name"] for code, info in target_langs.items()}

    def translate(self, text: str, target_lang: str, source_lang: str | None = None) -> str:
        src = source_lang or self.src_lang
        # Re-encode with the correct source language if different from default
        if src != self.src_lang:
            tokenizer = AutoTokenizer.from_pretrained(
                self.tokenizer.name_or_path, src_lang=src
            )
        else:
            tokenizer = self.tokenizer

        inputs = tokenizer(text, return_tensors="pt").to(self.device)
        forced_bos_token_id = tokenizer.convert_tokens_to_ids(target_lang)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=512,
                num_beams=4,
            )

        return tokenizer.decode(outputs[0], skip_special_tokens=True)

    def translate_batch(
        self, texts: list[str], target_lang: str, source_lang: str | None = None
    ) -> list[str]:
        src = source_lang or self.src_lang
        if src != self.src_lang:
            tokenizer = AutoTokenizer.from_pretrained(
                self.tokenizer.name_or_path, src_lang=src
            )
        else:
            tokenizer = self.tokenizer

        forced_bos_token_id = tokenizer.convert_tokens_to_ids(target_lang)
        results = []

        for text in texts:
            inputs = tokenizer(text, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    forced_bos_token_id=forced_bos_token_id,
                    max_length=512,
                    num_beams=4,
                )
            results.append(tokenizer.decode(outputs[0], skip_special_tokens=True))

        return results

    def translate_all(self, text: str) -> dict:
        results = {}
        for code in self.lang_codes:
            translated = self.translate(text, code)
            results[code] = {
                "lang_name": self.lang_name_map[code],
                "text": translated,
            }
        return results


def init_translator(model_name: str, device: str, src_lang: str, target_langs: dict):
    global _translator
    _translator = Translator(model_name, device, src_lang, target_langs)


def get_translator() -> Translator:
    global _translator
    if _translator is None:
        raise RuntimeError("Translator not initialized. Call init_translator() first.")
    return _translator
