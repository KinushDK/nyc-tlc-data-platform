import boto3
import pandas as pd
import io

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

    print(f"Row count: {len(df):,}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nDtypes:\n{df.dtypes}")
    print(f"\nNull counts:\n{df.isnull().sum()}")

    if "tpep_pickup_datetime" in df.columns:
        print(
            f"\nPickup date range: {df['tpep_pickup_datetime'].min()} to {df['tpep_pickup_datetime'].max()}"
        )

    print(f"\nFirst 3 rows:\n{df.head(3)}")
