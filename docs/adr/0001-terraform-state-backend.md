# ADR-0001: Terraform State Backend

## Status
Accepted

## Context
Terraform needs a place to keep track of what it's already built, so that running `terraform apply` again doesn't try to recreate everything from
scratch. On a team this state file also needs locking, so two people don't run Terraform at the same time and corrupt it. I'm working solo on this
project, but I wanted to set it up the way a real team would, since that's part of the point of this whole exercise.

## Decision
Went with the classic combo: an S3 bucket for the state file itself, and a DynamoDB table to handle locking.

- S3 bucket: `kinush02-tlc-platform-tfstate`
- Versioning: turned on, so if the state file ever gets overwritten with
  something broken, I can roll back to a previous version instead of losing track of everything Terraform manages
- DynamoDB table: `tlc-platform-tf-locks`, on-demand billing since it's
  barely going to get any traffic and I don't want to think about provisioned capacity for something this small
- Region: `us-east-1` for everything in this project, just to keep one consistent region instead of juggling multiple

## Alternatives Considered
**Terraform Cloud** — would've handled state storage and locking for me with basically no setup. Didn't go this way because part of the goal here
is to actually understand the AWS primitives underneath, not offload them to a third-party SaaS. If this were a real team project moving fast, I'd
probably reconsider.

**S3 native locking (`use_lockfile`), skipping DynamoDB entirely** Found out about this because Terraform threw a deprecation warning at me
the first time I ran `terraform plan`, telling me `dynamodb_table` is on its way out in favor of this newer approach. I looked into it and it's a
legitimate simpler option now. I stuck with DynamoDB anyway because it's still the pattern most production codebases and job descriptions reference,
and I'd rather be fluent in the version more people are actually using right now. Worth revisiting later once the native locking approach is more
established.

## Consequences
- State is recoverable if something goes wrong, thanks to versioning
- One extra resource (DynamoDB table) to manage, though it's effectively free at this scale
- From here on, every AWS resource in this project goes through Terraform - no manually clicking things into existence in the console, even for quick tests