"""
AWS Glue job version of the Gold-layer business marts for NYC Yellow
Taxi trip data. Same core logic as build_marts.py (local dev version),
adapted to run as a managed Glue job.
"""

import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F

args = getResolvedOptions(
    sys.argv, ["JOB_NAME", "silver_path", "lookup_path", "output_path"]
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)


def build_daily_trip_volume_by_borough(silver_df, zone_lookup_df):
    joined = silver_df.join(
        zone_lookup_df,
        silver_df.PULocationID == zone_lookup_df.LocationID,
        "left",
    )
    return (
        joined.withColumn("pickup_date", F.to_date("tpep_pickup_datetime"))
        .groupBy("pickup_date", "Borough")
        .agg(F.count("*").alias("trip_count"))
        .orderBy("pickup_date", "Borough")
    )


def build_daily_fare_tip_trends(silver_df):
    paid_trips = silver_df.filter(F.col("payment_type") != 0)
    return (
        paid_trips.withColumn("pickup_date", F.to_date("tpep_pickup_datetime"))
        .groupBy("pickup_date")
        .agg(
            F.round(F.avg("fare_amount"), 2).alias("avg_fare"),
            F.round(F.avg("tip_amount"), 2).alias("avg_tip"),
            F.count("*").alias("paid_trip_count"),
        )
        .orderBy("pickup_date")
    )


silver_df = spark.read.parquet(args["silver_path"])
zone_lookup_df = spark.read.option("header", "true").csv(args["lookup_path"])

trip_volume_mart = build_daily_trip_volume_by_borough(silver_df, zone_lookup_df)
fare_tip_mart = build_daily_fare_tip_trends(silver_df)

trip_volume_path = f"{args['output_path']}/daily_trip_volume_by_borough"
fare_tip_path = f"{args['output_path']}/daily_fare_tip_trends"

print(f"Writing trip volume mart to {trip_volume_path}")
trip_volume_mart.write.mode("overwrite").parquet(trip_volume_path)

print(f"Writing fare/tip mart to {fare_tip_path}")
fare_tip_mart.write.mode("overwrite").parquet(fare_tip_path)

job.commit()
