# Data Observations: NYC Yellow Taxi Trip Data (Jan-Mar 2025)

## Source
NYC TLC Trip Record Data, Yellow Taxi, downloaded from the official TLC CloudFront distribution (d37ci6vzurychx.cloudfront.net), landed in
`s3://kinush02-tlc-platform-bronze/raw/yellow/`.

## Summary by file

| File | Row count | Pickup date range | Notable issues |
|---|---|---|---|
| 2025-01.parquet | 3,475,226 | 2024-12-31 to 2025-02-01 | None — normal month-boundary spillover |
| 2025-02.parquet | 3,577,543 | 2025-01-31 to 2025-03-01 | None — normal month-boundary spillover |
| 2025-03.parquet | 4,145,257 | 2007-12-05 to 2025-04-01 | Contains at least one outlier pickup timestamp from 2007 — data entry error, needs filtering in Silver layer |

## Schema (20 columns, consistent across all 3 files)

| Column | Dtype | Notes |
|---|---|---|
| VendorID | int32 | |
| tpep_pickup_datetime | datetime64[us] | |
| tpep_dropoff_datetime | datetime64[us] | |
| passenger_count | float64 | ~916K nulls per file (~22-26% of rows) |
| trip_distance | float64 | |
| RatecodeID | float64 | Same ~916K nulls as passenger_count — likely same source rows |
| store_and_fwd_flag | object | Same ~916K nulls |
| PULocationID | int32 | |
| DOLocationID | int32 | |
| payment_type | int64 | |
| fare_amount | float64 | |
| extra | float64 | |
| mta_tax | float64 | |
| tip_amount | float64 | |
| tolls_amount | float64 | |
| improvement_surcharge | float64 | |
| total_amount | float64 | |
| congestion_surcharge | float64 | ~916K nulls |
| Airport_fee | float64 | ~916K nulls |
| cbd_congestion_fee | float64 | No nulls — new column added for 2025 (congestion pricing) |

## Key findings

1. **~916K rows per file are missing passenger_count, RatecodeID, store_and_fwd_flag, congestion_surcharge, and Airport_fee together** — this looks like a specific vendor or trip type that doesn't report these
   fields, not random missingness. Worth investigating by VendorID in Silver-layer work.

2. **March 2025 contains at least one severe timestamp outlier** (2007-12-05)— the Silver layer needs an explicit validation rule rejecting pickup timestamps outside a reasonable window around the file's expected month(e.g., ±3 days).

3. **`cbd_congestion_fee` is a new column starting in 2025**, related to NYC's congestion pricing program — has no nulls in this data, unlike the other surcharge columns.

4. Row counts range 3.4M-4.1M per month — at 12 months/year and 3 dataset types (Yellow/Green/HVFHV) eventually, this confirms the scale described in the brief and validates the choice to process this incrementally by month rather than loading everything at once.

## Next steps
- Investigate whether the ~916K null rows correlate with a specific VendorID or trip type
- Define and implement outlier rejection rules for the Silver layer
- Confirm schema consistency holds across additional months before scaling ingestion to the full 24-36 month range