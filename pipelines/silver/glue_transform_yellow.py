"""
AWS Glue job version of the Silver-layer transformation for NYC Yellow
Taxi trip data. Same core logic as transform_yellow.py (local dev version),
adapted to run as a managed Glue job.
"""

import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F

args = getResolvedOptions(
    sys.argv, ["JOB_NAME", "input_path", "output_path", "year", "month"]
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)


def enforce_schema(df):
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


year = int(args["year"])
month = int(args["month"])

df = spark.read.parquet(args["input_path"])
df = enforce_schema(df)
df = filter_outlier_timestamps(df, year, month)
df = df.dropDuplicates()

row_count = df.count()
print(f"Writing {row_count:,} rows to {args['output_path']}")

df.write.mode("overwrite").parquet(args["output_path"])

job.commit()
