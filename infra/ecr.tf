resource "aws_ecr_repository" "silver_transform" {
  name                 = "tlc-silver-transform"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}