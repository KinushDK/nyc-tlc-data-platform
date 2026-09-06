resource "aws_iam_role" "step_functions_role" {
  name = "tlc-platform-step-functions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "step_functions_glue_access" {
  name = "step-functions-glue-access"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "glue:StartJobRun",
        "glue:GetJobRun",
        "glue:GetJobRuns",
        "glue:BatchStopJobRun"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_sfn_state_machine" "silver_gold_pipeline" {
  name     = "tlc-silver-gold-pipeline"
  role_arn = aws_iam_role.step_functions_role.arn

  definition = file("${path.module}/../pipelines/orchestration/silver_gold_pipeline.asl.json")
}