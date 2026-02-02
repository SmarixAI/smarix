import json
import os
import boto3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
)

BUCKET = "smarix-data-apsouth1"
KEY = "Admin/state/runtime_state.json"


def update_curr_repo(owner: str, name: str):
    # 1. Fetch existing JSON
    response = s3.get_object(Bucket=BUCKET, Key=KEY)
    data = json.loads(response["Body"].read())

    # 2. Update only curr_repo
    data["curr_repo"] = {
        "owner": owner,
        "name": name
    }

    # Optional but recommended
    data["last_updated"] = datetime.utcnow().isoformat()

    # 3. Write back to S3
    s3.put_object(
        Bucket=BUCKET,
        Key=KEY,
        Body=json.dumps(data, indent=2),
        ContentType="application/json",
    )

    print("✅ curr_repo updated successfully")


if __name__ == "__main__":
    update_curr_repo(
        owner="CCExtractor",
        name="taskwarrior-flutter"
    )