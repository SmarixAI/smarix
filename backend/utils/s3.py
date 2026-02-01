import boto3
import json
from pathlib import Path


class S3Manager:
    def __init__(self, bucket: str, region: str = "ap-south-1"):
        self.bucket = bucket
        self.region = region
        self.s3 = boto3.client("s3", region_name=region)

    def upload_json(self, data: dict, key: str, public_read: bool = False):
        """Upload dict as JSON to S3 key."""
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        extra_args = {"ContentType": "application/json"}
        if public_read:
            extra_args["ACL"] = "public-read"
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=body, **extra_args)

    def download_json(self, key: str) -> dict:
        """Download JSON object from S3 key."""
        resp = self.s3.get_object(Bucket=self.bucket, Key=key)
        content = resp["Body"].read().decode("utf-8")
        return json.loads(content)

    def key_exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except:
            return False

    def get_public_url(self, key: str) -> str:
        """Return public S3 URL for the key."""
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

    def list_files(self, prefix: str = "") -> list:
        """
        List all files in the bucket with the given prefix.
        Returns a list of file keys (strings).
        """
        files = []
        try:
            paginator = self.s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        files.append(obj["Key"])
            return files
        except Exception as e:
            print(f"❌ Error listing S3 files: {e}")
            return []


s3_manager = S3Manager(bucket="smarix-data-apsouth1", region="ap-south-1")
