import io
import os
from pathlib import Path
import boto3
from dotenv import load_dotenv
import pandas as pd
import requests

load_dotenv()

client = boto3.client(
    "s3",
    endpoint_url="https://a3s.fi",
    aws_access_key_id=os.environ.get("ALLAS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("ALLAS_SECRET_ACCESS_KEY"),
)

UPLOADS = [
    {
        "local_dir": Path(r"D:\OneDrive - University of Oulu and Oamk\Railway-FMI-Data-CSV-Files-v2\matched_flat_data"),
        "bucket": "matched_flat_data",
    },
    {
        "local_dir": Path(r"D:\OneDrive - University of Oulu and Oamk\Railway-FMI-Data-CSV-Files-v2\weather_with_rolling_windows_data"),
        "bucket": "weather_data",
    },
]

for upload in UPLOADS:
    local_dir = upload["local_dir"]
    bucket = upload["bucket"]
    files = sorted(local_dir.glob("*.parquet"))
    print(f"\n=== Uploading {len(files)} files to bucket '{bucket}' ===")

    for path in files:
        raw = path.read_bytes()

        if raw[:4] != b"PAR1" or raw[-4:] != b"PAR1":
            print(f"  SKIP {path.name} — invalid local parquet file")
            continue

        size = len(raw)
        print(f"  {path.name} ({size:,} bytes) ...", end=" ", flush=True)
        presigned_url = client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": path.name},
            ExpiresIn=3600,
        )
        resp = requests.put(presigned_url, data=raw, headers={"Content-Length": str(size)})
        resp.raise_for_status()

        # Verify
        obj = client.get_object(Bucket=bucket, Key=path.name)
        remote = obj["Body"].read()
        if len(remote) == size and remote[-4:] == b"PAR1":
            print("OK")
        else:
            print(f"FAILED — remote {len(remote):,} bytes, last 4: {remote[-4:]}")

print("\nDone.")
