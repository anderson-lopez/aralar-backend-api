import os, uuid
from dataclasses import dataclass
import boto3


@dataclass
class PresignRequest:
    filename: str
    mime: str
    folder: str


@dataclass
class PresignResponse:
    upload_url: str
    public_url: str
    key: str


class StorageDriver:
    def presign_put(self, req: PresignRequest) -> PresignResponse:
        raise NotImplementedError


class S3Storage(StorageDriver):
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT"),
            aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
            region_name=os.getenv("S3_REGION", "us-east-1"),
        )
        self.bucket = os.getenv("S3_BUCKET", "aralar-media")
        self.public_base = os.getenv("S3_PUBLIC_BASE")  # ej: http://localhost:9000/aralar-media

    def presign_put(self, req: PresignRequest) -> PresignResponse:
        _key = f"{req.folder.rstrip('/')}/{uuid.uuid4()}-{req.filename}"
        upload_url = self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": _key, "ContentType": req.mime},
            ExpiresIn=300,
        )
        public_url = f"{self.public_base}/{_key}" if self.public_base else f"/s3/{_key}"
        return PresignResponse(upload_url=upload_url, public_url=public_url, key=_key)


def get_storage() -> StorageDriver:
    driver = os.getenv("STORAGE_DRIVER", "s3")
    if driver == "s3":
        return S3Storage()
    # Si más adelante agregas LocalStorage:
    # if driver == "local": return LocalStorage()
    return S3Storage()
