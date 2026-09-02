#!/bin/bash
set -euo pipefail

BUCKET="kinush02-tlc-platform-bronze"
MONTHS=("2025-01" "2025-02" "2025-03")

for month in "${MONTHS[@]}"; do
  echo "Downloading ${month}..."
  curl -sL "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_${month}.parquet" \
    -o "/tmp/yellow_tripdata_${month}.parquet"

  echo "Uploading ${month} to S3..."
  aws s3 cp "/tmp/yellow_tripdata_${month}.parquet" \
    "s3://${BUCKET}/raw/yellow/${month}.parquet"

  rm "/tmp/yellow_tripdata_${month}.parquet"
  echo "${month} done."
done

echo "All months uploaded."