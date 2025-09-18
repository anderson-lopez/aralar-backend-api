import os, uuid
from dataclasses import dataclass
import boto3
from botocore.config import Config as BotoConfig


@dataclass
class PresignRequest:
    filename: str
    mime: str


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
        self.public_base = os.getenv(
            "S3_PUBLIC_BASE"
        )  # ej: https://aralar-media.us-east-1.linodeobjects.com
        self.folder = os.getenv("S3_FOLDER", "menus")

    def presign_put(self, req: PresignRequest) -> PresignResponse:
        print("[s3] presign_put")

        _key = f"{self.folder.rstrip('/')}/{uuid.uuid4()}-{req.filename}"

        # Generate presigned URL for PUT operation with ACL
        expiration = int(os.getenv("S3_PRESIGN_EXPIRATION", "300"))
        upload_url = self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": _key,
                "ContentType": req.mime,
                "ACL": "public-read",  # 🔑 ACL incluido en la firma
            },
            ExpiresIn=expiration,
        )

        # Construct public URL for Linode Object Storage
        public_url = self._build_public_url(_key)

        return PresignResponse(upload_url=upload_url, public_url=public_url, key=_key)

    def make_object_public(self, key: str):
        """Make an uploaded object public by setting its ACL."""
        try:
            self.client.put_object_acl(
                Bucket=self.bucket,
                Key=key,
                ACL="public-read"
            )
            print(f"[s3] Made object public: {key}")
        except Exception as e:
            print(f"[s3] Failed to make object public: {e}")
            # No lanzamos excepción para no romper el flujo principal

    def _build_public_url(self, key: str) -> str:
        """Build public URL for accessing the uploaded file in Linode Object Storage."""
        if self.public_base:
            # Use explicit public base URL (recommended for Linode)
            return f"{self.public_base.rstrip('/')}/{key}"

        # Fallback: construct URL from endpoint and bucket
        endpoint = os.getenv("S3_ENDPOINT")
        if endpoint:
            # For Linode Object Storage, construct the public URL
            # Format: https://bucket-name.region.linodeobjects.com/key
            region = os.getenv("S3_REGION", "us-east-1")
            if "linodeobjects.com" in endpoint:
                return f"https://{self.bucket}.{region}.linodeobjects.com/{key}"
            else:
                # Generic S3-compatible endpoint
                return f"{endpoint.rstrip('/')}/{self.bucket}/{key}"

        # Last resort fallback
        return f"/s3/{key}"

    def upload_direct(self, *, fileobj, filename: str, folder: str) -> PresignResponse:
        """Upload file content directly to the bucket and return public URL and key."""
        print("[s3] upload_direct")
        print("[s3] bucket: ", self.bucket)
        print("[s3] endpoint: ", os.getenv("S3_ENDPOINT"))
        print("[s3] access_key: ", os.getenv("S3_ACCESS_KEY"))
        print("[s3] secret_key: ", os.getenv("S3_SECRET_KEY"))
        print("[s3] region: ", os.getenv("S3_REGION"))

        _key = f"{folder.rstrip('/')}/{uuid.uuid4()}-{filename}"
        self.client.put_object(
            Bucket=self.bucket,
            Key=_key,
            Body=fileobj,
            ACL="public-read",  # 🔑 CLAVE: Hace el archivo público
        )
        public_url = self._build_public_url(_key)
        return PresignResponse(upload_url="", public_url=public_url, key=_key)


def get_storage() -> StorageDriver:
    driver = os.getenv("STORAGE_DRIVER", "s3")
    if driver == "s3":
        return S3Storage()
    # Si más adelante agregas LocalStorage:
    # if driver == "local": return LocalStorage()
    return S3Storage()
