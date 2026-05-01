import os
import boto3

S3_BUCKET = os.environ.get("S3_BUCKET_NAME")
S3_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
S3_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

s3_client = None
if S3_BUCKET and S3_ACCESS_KEY and S3_SECRET_KEY:
    s3_client = boto3.client(
        "s3",
        region_name=S3_REGION,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
    )

def upload_file_to_s3(file_path, s3_key, mime_type=None):
    if not s3_client:
        return False
    try:
        ExtraArgs = {}
        if mime_type:
            ExtraArgs['ContentType'] = mime_type
        # If your bucket has block public access, you might need to omit ACL
        # but for typical public media we'd use 'public-read' if ACLs are enabled.
        # ExtraArgs['ACL'] = 'public-read' 
        s3_client.upload_file(file_path, S3_BUCKET, s3_key, ExtraArgs=ExtraArgs)
        return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
    except Exception as e:
        print("S3 Upload Error:", e)
        return False

def delete_file_from_s3(s3_key):
    if not s3_client:
        return False
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        return True
    except Exception as e:
        print("S3 Delete Error:", e)
        return False
