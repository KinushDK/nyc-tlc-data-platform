"""
Gold-layer business marts for NYC Yellow Taxi trip data.

Reads Silver-layer cleaned data plus the taxi zone lookup reference table,
and builds two business marts:
  1. Daily trip volume by pickup borough
  2. Daily average fare and tip amount

Local development version — run directly with `python build_marts.py`.
"""

import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def build_spark_session(app_name: str = "gold-yellow-marts") -> SparkSession:
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    hadoop_conf = spark._jsc.hadoopConfiguration()
    hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    return spark


def read_silver(spark: SparkSession, silver_path: str):
    return spark.read.parquet(silver_path)


def read_zone_lookup(spark: SparkSession, lookup_path: str):
    return spark.read.option("header", "true").csv(lookup_path)


def build_daily_trip_volume_by_borough(silver_df, zone_lookup_df):
    """Mart 1: daily trip count, grouped by pickup date and borough."""
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
    """
    Mart 2: daily average fare and tip, excluding payment_type=0 trips
    (no-charge/voided fares, per the earlier data investigation - including
    them would skew average fare/tip downward with non-representative $0s).
    """
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


def main(silver_path: str, lookup_path: str, output_base_path: str):
    spark = build_spark_session()

    silver_df = read_silver(spark, silver_path)
    zone_lookup_df = read_zone_lookup(spark, lookup_path)

    trip_volume_mart = build_daily_trip_volume_by_borough(silver_df, zone_lookup_df)
    fare_tip_mart = build_daily_fare_tip_trends(silver_df)

    trip_volume_path = f"{output_base_path}/daily_trip_volume_by_borough"
    fare_tip_path = f"{output_base_path}/daily_fare_tip_trends"

    print(f"Writing trip volume mart to {trip_volume_path}")
    trip_volume_mart.write.mode("overwrite").parquet(trip_volume_path)

    print(f"Writing fare/tip mart to {fare_tip_path}")
    fare_tip_mart.write.mode("overwrite").parquet(fare_tip_path)

    spark.stop()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: build_marts.py <silver_path> <lookup_path> <output_base_path>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2], sys.argv[3])
