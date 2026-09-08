data "aws_iam_policy_document" "spark_irsa_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    principals {
      type        = "Federated"
      identifiers = [module.eks.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${module.eks.oidc_provider}:sub"
      values   = ["system:serviceaccount:spark-jobs:spark-jobs-sa"]
    }

    condition {
      test     = "StringEquals"
      variable = "${module.eks.oidc_provider}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "spark_irsa_role" {
  name               = "tlc-platform-spark-irsa-role"
  assume_role_policy = data.aws_iam_policy_document.spark_irsa_assume_role.json
}

resource "aws_iam_role_policy" "spark_irsa_s3_access" {
  name = "spark-irsa-s3-access"
  role = aws_iam_role.spark_irsa_role.id

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