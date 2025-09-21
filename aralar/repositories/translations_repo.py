from datetime import datetime
from hashlib import sha1


class TranslationsRepo:
    def __init__(self, db):
        self.col = db["translations_cache"]
        self.col.create_index([("hash", 1)], unique=True)

    @staticmethod
    def make_hash(text: str, src: str, tgt: str, provider: str, glossary_version: int | None):
        key = f"{text}\u241f{src}\u241f{tgt}\u241f{provider}\u241f{glossary_version or 0}"
        return sha1(key.encode("utf-8")).hexdigest()

    def get(self, h: str):
        return self.col.find_one({"hash": h})

    def put(self, h: str, doc: dict):
        doc["hash"] = h
        doc["created_at"] = datetime.utcnow()
        try:
            self.col.insert_one(doc)
        except Exception:
            pass
