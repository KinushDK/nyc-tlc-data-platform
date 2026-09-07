# IAM role that Glue jobs will assume to read/write S3 and update the catalog
resource "aws_iam_role" "glue_job_role" {
  name = "tlc-platform-glue-job-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "glue.amazonaws.com"
      }
    }]
  })
}

# AWS-managed policy covering standard Glue service permissions
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_job_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# Custom policy: allow this role to read/write our Bronze and Silver buckets
resource "aws_iam_role_policy" "glue_s3_access" {
  name = "glue-s3-access"
  role = aws_iam_role.glue_job_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ]
      Resource = [
        aws_s3_bucket.bronze.arn,
        "${aws_s3_bucket.bronze.arn}/*",
        aws_s3_bucket.silver.arn,
        "${aws_s3_bucket.silver.arn}/*",
        aws_s3_bucket.gold.arn,
        "${aws_s3_bucket.gold.arn}/*"
      ]
    }]
  })
}

# The Glue Data Catalog database - acts as the "namespace" for tables
resource "aws_glue_catalog_database" "tlc_platform" {
  name = "tlc_platform"
}

resource "aws_glue_job" "silver_yellow_transform" {
  name     = "silver-yellow-taxi-transform"
  role_arn = aws_iam_role.glue_job_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://kinush02-tlc-platform-bronze/scripts/glue_transform_yellow.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-metrics"                   = "true"
  }

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 30
}

resource "aws_glue_job" "gold_yellow_marts" {
  name     = "gold-yellow-taxi-marts"
  role_arn = aws_iam_role.glue_job_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://kinush02-tlc-platform-bronze/scripts/glue_build_marts.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-metrics"                   = "true"
  }

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 30
}

resource "aws_glue_catalog_table" "daily_trip_volume_by_borough" {
  name          = "daily_trip_volume_by_borough"
  database_name = aws_glue_catalog_database.tlc_platform.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification" = "parquet"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.gold.id}/yellow/2025-02/daily_trip_volume_by_borough/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "pickup_date"
      type = "date"
    }
    columns {
      name = "borough"
      type = "string"
    }
    columns {
      name = "trip_count"
      type = "bigint"
    }
  }
}

resource "aws_glue_catalog_table" "daily_fare_tip_trends" {
  name          = "daily_fare_tip_trends"
  database_name = aws_glue_catalog_database.tlc_platform.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification" = "parquet"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.gold.id}/yellow/2025-02/daily_fare_tip_trends/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "pickup_date"
      type = "date"
    }
    columns {
      name = "avg_fare"
      type = "double"
    }
    columns {
      name = "avg_tip"
      type = "double"
    }
    columns {
      name = "paid_trip_count"
      type = "bigint"
    }
  }
}