"""
S3 storage helpers — gracefully degrades if boto3 is not installed
or S3 credentials are not configured.
"""

import os

try:
    import boto3
    _BOTO3_AVAILABLE = True
except ImportError:
    _BOTO3_AVAILABLE = False

S3_BUCKET = os.environ.get("S3_BUCKET_NAME")
S3_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
S3_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

s3_client = None
if _BOTO3_AVAILABLE and S3_BUCKET and S3_ACCESS_KEY and S3_SECRET_KEY:
    try:
        s3_client = boto3.client(
            "s3",
            region_name=S3_REGION,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
        )
    except Exception as e:
        print(f"[S3] Failed to create client: {e}")


def upload_file_to_s3(file_path, s3_key, mime_type=None):
    if not s3_client:
        return False
    try:
        extra_args = {}
        if mime_type:
            extra_args["ContentType"] = mime_type
        s3_client.upload_file(file_path, S3_BUCKET, s3_key, ExtraArgs=extra_args)
        return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
    except Exception as e:
        print(f"[S3] Upload error: {e}")
        return False


def delete_file_from_s3(s3_key):
    if not s3_client:
        return False
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        return True
    except Exception as e:
        print(f"[S3] Delete error: {e}")
        return False
