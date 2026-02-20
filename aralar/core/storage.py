import os, uuid
from dataclasses import dataclass
import boto3
from botocore.config import Config as BotoConfig

# --- CAMBIOS REALIZADOS PARA AWS S3 (Febrero 2026) ---
# 1. Se ajustó la región por defecto a 'us-east-2' (Ohio) según la consola de AWS del usuario.
# 2. Se incluyó 'ACL': 'public-read' en la firma del presigned_url. 
#    ESTO REQUIERE: Habilitar ACLs en la consola de AWS (Pestaña Permisos > Propiedad de objetos).
# 3. Se corrigió _build_public_url para usar el formato oficial de Amazon S3.
# 4. Se eliminaron las referencias forzadas a linodeobjects.com.
# ----------------------------------------------------

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
        # Configuración del cliente usando las variables del .env
        self.client = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT"),
            aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
            region_name=os.getenv("S3_REGION", "us-east-2"),
        )
        self.bucket = os.getenv("S3_BUCKET", "aralar-bucket")
        self.public_base = os.getenv("S3_PUBLIC_BASE") 
        self.folder = os.getenv("S3_FOLDER", "menus")

    def presign_put(self, req: PresignRequest) -> PresignResponse:
        print(f"[s3] Generando presign_put para el bucket: {self.bucket}")

        _key = f"{self.folder.rstrip('/')}/{uuid.uuid4()}-{req.filename}"

        # Parámetros para la URL firmada
        # Se incluye ACL para evitar el error 'HeadersNotSigned: x-amz-acl' en el proxy-put
        params = {
            "Bucket": self.bucket,
            "Key": _key,
            "ContentType": req.mime,
            "ACL": "public-read",
        }

        expiration = int(os.getenv("S3_PRESIGN_EXPIRATION", "300"))
        
        upload_url = self.client.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=expiration,
        )

        # Construcción de la URL pública para mostrar la imagen
        public_url = self._build_public_url(_key)

        return PresignResponse(upload_url=upload_url, public_url=public_url, key=_key)

    def make_object_public(self, key: str):
        """Asegura que un objeto sea público mediante ACL."""
        try:
            self.client.put_object_acl(
                Bucket=self.bucket,
                Key=key,
                ACL="public-read"
            )
            print(f"[s3] Objeto marcado como público: {key}")
        except Exception as e:
            print(f"[s3] Error al intentar hacer público el objeto: {e}")

    def _build_public_url(self, key: str) -> str:
        """Construye la URL pública de acceso según el estándar de Amazon S3."""
        if self.public_base:
            return f"{self.public_base.rstrip('/')}/{key}"

        # Formato: https://bucket.s3.region.amazonaws.com/key
        region = os.getenv("S3_REGION", "us-east-2")
        return f"https://{self.bucket}.s3.{region}.amazonaws.com/{key}"

    def upload_direct(self, *, fileobj, filename: str, folder: str) -> PresignResponse:
        """Sube contenido directamente al bucket (usado en proxy-put interno)."""
        print("[s3] Ejecutando upload_direct")
        _key = f"{folder.rstrip('/')}/{uuid.uuid4()}-{filename}"
        
        self.client.put_object(
            Bucket=self.bucket,
            Key=_key,
            Body=fileobj,
            ACL="public-read",
        )
        
        public_url = self._build_public_url(_key)
        return PresignResponse(upload_url="", public_url=public_url, key=_key)

def get_storage() -> StorageDriver:
    driver = os.getenv("STORAGE_DRIVER", "s3")
    if driver == "s3":
        return S3Storage()
    return S3Storage()