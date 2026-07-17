import boto3
import json
import os
from datetime import datetime
from typing import Optional
from backend.app.core.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )


def ensure_bucket_exists(bucket: str):
    """Creates bucket if it doesn't exist — idempotent."""
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=bucket)
    except Exception:
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": settings.aws_region},
        )
        # block all public access — security requirement
        s3.put_public_access_block(
            Bucket=bucket,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
        print(f"[S3] Created bucket: {bucket}")


def upload_artifact(
    content: str,
    artifact_type: str,
    task_id: str,
    metadata: Optional[dict] = None,
) -> str:
    """
    Uploads agent output as an artifact to S3.
    Returns the S3 key for the artifact.
    Structure: artifacts/{artifact_type}/{task_id}/{timestamp}.json
    """
    s3 = get_s3_client()
    bucket = settings.aws_s3_bucket
    ensure_bucket_exists(bucket)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    key = f"artifacts/{artifact_type}/{task_id}/{timestamp}.json"

    payload = {
        "task_id": task_id,
        "artifact_type": artifact_type,
        "content": content,
        "timestamp": timestamp,
        "metadata": metadata or {},
    }

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, indent=2),
        ContentType="application/json",
        ServerSideEncryption="AES256",    # encrypt at rest — security requirement
    )

    s3_url = f"s3://{bucket}/{key}"
    print(f"[S3] Uploaded artifact: {s3_url}")
    return s3_url


def list_artifacts(artifact_type: str = None, task_id: str = None) -> list:
    """Lists artifacts in S3 with optional filtering."""
    s3 = get_s3_client()
    prefix = "artifacts/"
    if artifact_type:
        prefix += f"{artifact_type}/"
    if task_id:
        prefix += f"{task_id}/"

    try:
        response = s3.list_objects_v2(Bucket=settings.aws_s3_bucket, Prefix=prefix)
        return [
            {
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            }
            for obj in response.get("Contents", [])
        ]
    except Exception:
        return []


def get_artifact(key: str) -> Optional[dict]:
    """Downloads and returns artifact content from S3."""
    s3 = get_s3_client()
    try:
        response = s3.get_object(Bucket=settings.aws_s3_bucket, Key=key)
        return json.loads(response["Body"].read())
    except Exception:
        return None


def generate_presigned_url(key: str, expiry: int = 3600) -> str:
    """
    Generates a temporary signed URL for sharing artifacts.
    Expires after expiry seconds — secure, no permanent public access.
    """
    s3 = get_s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.aws_s3_bucket, "Key": key},
        ExpiresIn=expiry,
    )