"""
Silver-layer transformation for NYC Yellow Taxi trip data.

Reads raw Bronze Parquet, applies schema enforcement, filters out
timestamp outliers, deduplicates, and writes clean output to Silver.

Local development version — run directly with `python transform_yellow.py`.
Will be adapted into an AWS Glue job script in a later step.
"""

import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def build_spark_session(app_name: str = "silver-yellow-transform") -> SparkSession:
    spark = SparkSession.builder.appName(app_name).getOrCreate()

    hadoop_conf = spark._jsc.hadoopConfiguration()
    hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

    return spark


def read_bronze(spark: SparkSession, input_path: str):
    return spark.read.parquet(input_path)


def enforce_schema(df):
    """Cast columns to explicit, consistent types."""
    return df.select(
        F.col("VendorID").cast("int"),
        F.col("tpep_pickup_datetime").cast("timestamp"),
        F.col("tpep_dropoff_datetime").cast("timestamp"),
        F.col("passenger_count").cast("int"),
        F.col("trip_distance").cast("double"),
        F.col("RatecodeID").cast("int"),
        F.col("store_and_fwd_flag").cast("string"),
        F.col("PULocationID").cast("int"),
        F.col("DOLocationID").cast("int"),
        F.col("payment_type").cast("int"),
        F.col("fare_amount").cast("double"),
        F.col("extra").cast("double"),
        F.col("mta_tax").cast("double"),
        F.col("tip_amount").cast("double"),
        F.col("tolls_amount").cast("double"),
        F.col("improvement_surcharge").cast("double"),
        F.col("total_amount").cast("double"),
        F.col("congestion_surcharge").cast("double"),
        F.col("Airport_fee").cast("double"),
        F.col("cbd_congestion_fee").cast("double"),
    )


def filter_outlier_timestamps(df, expected_year: int, expected_month: int):
    """
    Reject rows where pickup timestamp is wildly outside the expected
    month (e.g. the 2007 outlier found in March 2025 data). Allow a small
    buffer either side of the month boundary for legitimate spillover.
    """
    return df.filter(
        (F.year("tpep_pickup_datetime") == expected_year)
        & (F.month("tpep_pickup_datetime") == expected_month)
        | (
            F.abs(
                F.datediff(
                    F.col("tpep_pickup_datetime"),
                    F.to_date(F.lit(f"{expected_year}-{expected_month:02d}-01")),
                )
            )
            <= 3
        )
    )


def deduplicate(df):
    return df.dropDuplicates()


def write_silver(df, output_path: str):
    df.write.mode("overwrite").parquet(output_path)


def main(input_path: str, output_path: str, year: int, month: int):
    spark = build_spark_session()

    df = read_bronze(spark, input_path)
    df = enforce_schema(df)
    df = filter_outlier_timestamps(df, year, month)
    df = deduplicate(df)

    row_count = df.count()
    print(f"Writing {row_count:,} rows to {output_path}")

    write_silver(df, output_path)

    spark.stop()


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: transform_yellow.py <input_path> <output_path> <year> <month>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
