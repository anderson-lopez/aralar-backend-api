import os, uuid
from dataclasses import dataclass
import boto3
from botocore.config import Config as BotoConfig


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
        cfg = BotoConfig(s3={"addressing_style": "path"}, signature_version="s3v4")
        self.client = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT"),
            aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
            region_name=os.getenv("S3_REGION", "us-east-1"),
            config=cfg,
        )
        self.bucket = os.getenv("S3_BUCKET", "aralar-media")
        self.public_base = os.getenv("S3_PUBLIC_BASE")  # ej: http://localhost:9000/aralar-media

    def presign_put(self, req: PresignRequest) -> PresignResponse:
        print("[s3] presign_put")
        print("[s3] bucket: ", self.bucket)
        print("[s3] endpoint: ", os.getenv("S3_ENDPOINT"))
        print("[s3] access_key: ", os.getenv("S3_ACCESS_KEY"))
        print("[s3] secret_key: ", os.getenv("S3_SECRET_KEY"))
        print("[s3] region: ", os.getenv("S3_REGION"))
        _key = f"{req.folder.rstrip('/')}/{uuid.uuid4()}-{req.filename}"
        upload_url = self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": _key, "ContentType": req.mime},
            ExpiresIn=300,
        )  # http://localhost:9000/aralar-media/menus/817af297-57ab-48e2-9580-ceea4d598d7e-Disconect%20rabbit.PNG?AWSAccessKeyId=minioadmin&Signature=7fswM8MDS%2FbpRiKm1zhpTWXJnmQ%3D&content-type=image%2Fpng&Expires=1757891191
        public_url = f"{self.public_base}/{_key}" if self.public_base else f"/s3/{_key}"
        return PresignResponse(upload_url=upload_url, public_url=public_url, key=_key)

    def upload_direct(self, *, fileobj, filename: str, mime: str, folder: str) -> PresignResponse:
        """Upload file content directly to the bucket and return public URL and key."""
        print("[s3] upload_direct")
        print("[s3] bucket: ", self.bucket)
        print("[s3] endpoint: ", os.getenv("S3_ENDPOINT"))
        print("[s3] access_key: ", os.getenv("S3_ACCESS_KEY"))
        print("[s3] secret_key: ", os.getenv("S3_SECRET_KEY"))
        print("[s3] region: ", os.getenv("S3_REGION"))

        _key = f"{folder.rstrip('/')}/{uuid.uuid4()}-{filename}"
        self.client.put_object(Bucket=self.bucket, Key=_key, Body=fileobj, ContentType=mime)
        public_url = f"{self.public_base}/{_key}" if self.public_base else f"/s3/{_key}"
        return PresignResponse(upload_url="", public_url=public_url, key=_key)


def get_storage() -> StorageDriver:
    driver = os.getenv("STORAGE_DRIVER", "s3")
    if driver == "s3":
        return S3Storage()
    # Si más adelante agregas LocalStorage:
    # if driver == "local": return LocalStorage()
    return S3Storage()
