resource "aws_cloudwatch_dashboard" "tlc_platform" {
  dashboard_name = "tlc-platform-pipeline"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Glue Job Success/Failure Count"
          view   = "timeSeries"
          region = "us-east-1"
          metrics = [
            ["Glue", "glue.driver.aggregate.numCompletedTasks", "Type", "count", "JobRunId", "ALL", "JobName", "silver-yellow-taxi-transform"],
            ["Glue", "glue.driver.aggregate.numFailedTasks", "Type", "count", "JobRunId", "ALL", "JobName", "silver-yellow-taxi-transform"],
            ["Glue", "glue.driver.aggregate.numCompletedTasks", "Type", "count", "JobRunId", "ALL", "JobName", "gold-yellow-taxi-marts"],
            ["Glue", "glue.driver.aggregate.numFailedTasks", "Type", "count", "JobRunId", "ALL", "JobName", "gold-yellow-taxi-marts"]
          ]
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Step Functions Execution Status"
          view   = "timeSeries"
          region = "us-east-1"
          metrics = [
            ["AWS/States", "ExecutionsSucceeded", "StateMachineArn", aws_sfn_state_machine.silver_gold_pipeline.arn],
            ["AWS/States", "ExecutionsFailed", "StateMachineArn", aws_sfn_state_machine.silver_gold_pipeline.arn]
          ]
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Glue Job Duration"
          view   = "timeSeries"
          region = "us-east-1"
          metrics = [
            ["Glue", "glue.driver.aggregate.elapsedTime", "Type", "count", "JobRunId", "ALL", "JobName", "silver-yellow-taxi-transform"],
            ["Glue", "glue.driver.aggregate.elapsedTime", "Type", "count", "JobRunId", "ALL", "JobName", "gold-yellow-taxi-marts"]
          ]
          period = 300
          stat   = "Average"
        }
      }
    ]
  })
}