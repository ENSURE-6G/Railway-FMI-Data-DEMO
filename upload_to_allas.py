import os
import re
from pathlib import Path
import boto3
from dotenv import load_dotenv
import requests

load_dotenv()

client = boto3.client(
    "s3",
    endpoint_url="https://a3s.fi",
    aws_access_key_id=os.environ.get("ALLAS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("ALLAS_SECRET_ACCESS_KEY"),
)

DATE_START = (2018, 1)
DATE_END   = (2022, 12)

UPLOADS = [
    {
        "local_dir": Path(r"D:\OneDrive - University of Oulu and Oamk\Railway-FMI-Data-CSV-Files-v2\matched_flat_data"),
        "bucket": "matched_flat_data",
    },
]

def in_range(filename):
    m = re.search(r"(\d{4})_(\d{2})\.parquet$", filename)
    if not m:
        return False
    return DATE_START <= (int(m.group(1)), int(m.group(2))) <= DATE_END

for upload in UPLOADS:
    local_dir = upload["local_dir"]
    bucket = upload["bucket"]
    files = [p for p in sorted(local_dir.glob("*.parquet")) if in_range(p.name)]
    print(f"\n=== Uploading {len(files)} files to bucket '{bucket}' ({DATE_START[0]}-{DATE_START[1]:02d} -> {DATE_END[0]}-{DATE_END[1]:02d}) ===")

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
