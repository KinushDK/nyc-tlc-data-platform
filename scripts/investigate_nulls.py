import io

import boto3
import pandas as pd

BUCKET = "kinush02-tlc-platform-bronze"
FILES = [
    "raw/yellow/2025-01.parquet",
    "raw/yellow/2025-02.parquet",
    "raw/yellow/2025-03.parquet",
]

s3 = boto3.client("s3")

for key in FILES:
    print(f"\n{'='*60}")
    print(f"FILE: {key}")
    print("=" * 60)

    obj = s3.get_object(Bucket=BUCKET, Key=key)
    df = pd.read_parquet(io.BytesIO(obj["Body"].read()))

    null_mask = df["passenger_count"].isnull()

    print("\nVendorID breakdown for NULL rows:")
    print(df[null_mask]["VendorID"].value_counts())

    print("\nVendorID breakdown for NON-NULL rows:")
    print(df[~null_mask]["VendorID"].value_counts())

    print("\npayment_type breakdown for NULL rows:")
    print(df[null_mask]["payment_type"].value_counts())

    print("\nSample of NULL rows (first 3):")
    print(df[null_mask].head(3))
