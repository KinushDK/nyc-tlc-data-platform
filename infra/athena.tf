resource "aws_athena_workgroup" "tlc_platform" {
  name = "tlc-platform-workgroup"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.gold.id}/athena-query-results/"
    }
  }
}