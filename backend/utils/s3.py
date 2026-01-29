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


s3_manager = S3Manager(bucket="smarix-data", region="us-east-1")
