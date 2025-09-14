import os, json, boto3, botocore
from dotenv import load_dotenv
import sys

# Load .env before importing Config so BaseConfig reads updated environment
load_dotenv()
# Ensure project root (one level up) is on sys.path when running from scripts/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from aralar.config import BaseConfig as Config

# docker compose up -d minio
# $env:S3_ENDPOINT="http://localhost:9000"
# $env:S3_ACCESS_KEY="minio"
# $env:S3_SECRET_KEY="minio123"
# $env:S3_REGION="us-east-1"
# $env:S3_BUCKET="aralar-media"
# python scripts/s3_bootstrap.py


def client():
    cfg = Config
    return boto3.client(
        "s3",
        endpoint_url=cfg.S3_ENDPOINT,
        aws_access_key_id=cfg.S3_ACCESS_KEY,
        aws_secret_access_key=cfg.S3_SECRET_KEY,
        region_name=cfg.S3_REGION,
    )


def ensure_bucket():
    s3 = client()
    bucket = Config.S3_BUCKET
    try:
        s3.head_bucket(Bucket=bucket)
        print(f"[s3] bucket exists: {bucket}")
    except botocore.exceptions.ClientError:
        s3.create_bucket(Bucket=bucket)
        print(f"[s3] bucket created: {bucket}")

    # CORS: permitir PUT presign desde tu front y GET público
    cors = {
        "CORSRules": [
            {
                "AllowedHeaders": ["*"],
                "AllowedMethods": ["GET", "PUT"],
                "AllowedOrigins": ["*"],  # en prod: limita a tu dominio(s)
                "ExposeHeaders": ["ETag"],
                "MaxAgeSeconds": 3600,
            }
        ]
    }
    s3.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors)
    print("[s3] CORS applied")

    # Policy: lectura pública (GET) (en prod puedes servir por CDN en vez de policy pública)
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicRead",
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket}/*"],
            }
        ],
    }
    s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
    print("[s3] public read policy applied")


if __name__ == "__main__":
    ensure_bucket()
