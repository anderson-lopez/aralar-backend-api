import os
from typing import Tuple
from ..core.storage import get_storage, PresignRequest


class UploadsService:
    def __init__(self):
        self.storage = get_storage()
        self.max_mb = int(os.getenv("UPLOADS_MAX_MB", "5"))
        self.mime_whitelist = set(
            (os.getenv("UPLOADS_MIME_WHITELIST", "image/jpeg,image/png,image/webp")).split(",")
        )

    def _validate(self, filename: str, mime: str) -> Tuple[bool, str]:
        if mime not in self.mime_whitelist:
            return False, f"mime not allowed ({mime})"
        # tamaño se valida del lado del cliente al PUT; aquí solo límite razonable si mandas size
        return True, ""

    def presign(self, filename: str, mime: str, folder: str):
        ok, err = self._validate(filename, mime)
        if not ok:
            raise ValueError(err)
        req = PresignRequest(filename=filename, mime=mime, folder=folder or "menus")
        resp = self.storage.presign_put(req)
        return {"upload_url": resp.upload_url, "public_url": resp.public_url, "key": resp.key}
