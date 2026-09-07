# Runbook: NYC TLC Data Platform — Track A

## 1. Deploying the Platform from Scratch

1. Clone the repository:  
   `git clone https://github.com/KinushDK/nyc-tlc-data-platform.git`

2. Create an AWS account if you don’t already have one. Make sure the account is fully registered and your payment method is verified before proceeding. Some services, including Glue, can be restricted on accounts that haven’t completed this step.

3. Secure the account: enable MFA on the root user and avoid using root for day-to-day tasks.

4. Create an IAM admin user with both console and CLI access, and enable MFA on this user as well.

5. Enable IAM access to billing information. By default, even users with `AdministratorAccess` cannot see billing. You can either:
   - Enable “IAM User and Role Access to Billing Information” in the root account settings, or  
   - Attach the `AWSBillingReadOnlyAccess` policy to your IAM user.

6. Install and configure the AWS CLI:  
   `aws configure`  
   Verify with:  
   `aws sts get-caller-identity`

7. Set up a monthly budget alert in the Billing console (Billing → Budgets) before creating any resources.

8. Bootstrap the Terraform backend manually (one-time setup, outside of Terraform):
   - Create the S3 state bucket and DynamoDB lock table as described in ADR-0001.

9. Complete the AWS Glue “Prepare your account” wizard (Glue console → Getting Started). This grants IAM users and roles the necessary Glue console access and S3 permissions at the account level. Without this step, `terraform apply` will fail on any `aws_glue_job` resource, even with full IAM permissions.

10. Run the following in the `infra/` directory:  
    - `terraform init`  
    - `terraform apply`  
    This creates all S3 buckets, IAM roles, the Glue Data Catalog database, Glue jobs, and the Step Functions state machine.

11. Upload the transformation scripts to S3 if they are not already present:  
    `aws s3 cp pipelines/silver/glue_transform_yellow.py s3://.../scripts/`  
    (Repeat for the Gold script once it exists as a Glue job.)

12. Run `scripts/pull_bronze_data.sh` to load the initial raw data into the Bronze bucket.

***

## 2. Adding a New Month of Data

1. Edit `scripts/pull_bronze_data.sh` and update the `MONTHS` array to include the new month.

2. Run the script to pull and upload the new raw file to:  
   `s3://.../raw/yellow/`

3. Trigger the pipeline for that month. You can either:
   - Start a Step Functions execution manually via the console or CLI, passing `year`, `month`, and input/output paths as the execution input, or  
   - Run the Silver and Gold Glue jobs manually with the same arguments (useful for debugging a single month in isolation).

4. Verify success:
   - Check the Step Functions execution graph to confirm both steps completed successfully (green).
   - Confirm that new Parquet files exist in `s3://.../silver/` and `s3://.../gold/` for that month.
   - Run a quick Athena query against the new month’s data to sanity-check row counts.

***

## 3. Recovering from a Failed Glue Job Run

1. Check the Step Functions console. The execution graph will show exactly which state failed (`RunSilverTransform` or `RunGoldTransform`).

2. Click into the failed state to see the error details. It will link directly to the Glue job run and the relevant CloudWatch logs.

3. The state machine already retries the Silver job twice with exponential backoff (30 seconds, then 60 seconds) before giving up. If you’re looking at a `SilverFailed` state, those retries have already been exhausted.

4. Common failure causes to check first:
   - A malformed or unexpected schema in that month’s source file.
   - An IAM permission gap, especially if buckets were recently added.
   - A Glue job timeout (currently set to 30 minutes). Increase this if larger data volumes need more time.

5. Fix the underlying issue, then re-run the Step Functions execution for that month. Silver’s `write.mode("overwrite")` means it’s safe to simply re-run; no manual cleanup is required.

***

## 4. Recovering from a Partial Terraform Apply

Real scenario from this project: `terraform apply` successfully created 3 of 4 planned resources, then failed on the 4th due to an AWS-side `AccessDeniedException` (unrelated to Terraform itself).

1. Don’t panic or try to manually recreate what already succeeded. Terraform’s state file already tracks what was created.

2. Run `terraform plan` to confirm exactly what’s still pending. It will only show the resource(s) that failed, not the ones that succeeded.

3. Fix the actual blocker (in this case, an AWS Support case, not a configuration change).

4. Once resolved, re-run `terraform apply`. It will only attempt to create the remaining resource(s).

***

## 5. Rolling Back a Bad Data Load

If a month’s Silver or Gold output turns out to be incorrect (e.g., unexpected schema drift, a new outlier pattern not yet handled, or a logic bug):

1. Fix the transformation script (add the new validation rule or handle the new edge case).

2. Re-run the Glue job (or Step Functions execution) for that specific month only. There is no separate “rollback” step, because every job uses `write.mode("overwrite")` on that month’s output path. Re-running with the corrected logic simply replaces the bad output.

3. This is a deliberate design choice, not a missing feature. It makes the pipeline idempotent and safe to re-run, avoiding the need for complex versioned rollback logic.

***

## 6. Known Operational Gotchas

- **New AWS accounts can hit `AccessDeniedException` on services like Glue and Cost Explorer even with `AdministratorAccess` attached.**  
  This is an account-level restriction, not an IAM issue. Adding more IAM policies won’t fix it. The solution is to open an AWS Support case. Expect some delay, and plan other work around it rather than blocking.

- **IAM users cannot see Billing or Cost Explorer by default, even as admins.**  
  You must either:
  - Enable “IAM User and Role Access to Billing Information” as root, or  
  - Attach the `AWSBillingReadOnlyAccess` policy directly to the IAM user.

- **Local PySpark on Windows requires Java 17 specifically.**  
  Newer versions (tested: Java 24) are incompatible with Spark’s bundled Hadoop libraries and fail with errors like `getSubject is not supported`. Install Java 17 alongside any newer version, and set `JAVA_HOME` for the terminal session instead of changing the system default.

- **Reading/writing S3 from local PySpark requires matching `hadoop-aws` and AWS SDK jar versions to the Hadoop version PySpark actually bundles.**  
  Check the bundled version with:  
  `find <pyspark-install>/jars -iname "hadoop-client-api*"`  
  Mismatched versions can cause a cascade of seemingly unrelated errors (`ClassNotFoundException`, `NumberFormatException`, credential provider class errors) before you land on a working combination.

- **AWS credentials for local Spark S3 access need to be exported as environment variables:**  
  `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.  
  Spark’s default Hadoop credential chain does not automatically read the AWS CLI’s `~/.aws/credentials` file.

- **AWS CloudWatch custom metrics with multiple dimensions require an exact match on all dimensions, not just one.**
For example, Glue publishes glue.driver.aggregate.numCompletedTasks with three dimensions together: Type, JobRunId, and JobName. If you filter a dashboard widget by JobName alone, it silently returns no data, even though the metric genuinely exists.
Use aws cloudwatch list-metrics to see the real dimension set for a metric before writing dashboard JSON, rather than guessing. The JobRunId = "ALL" value aggregates across all runs of a job — this is the right choice for a permanent dashboard, instead of hardcoding one specific run ID.

- **A Terraform-managed CloudWatch dashboard can silently drift if edited via the console.**
Adding a widget through the console UI and clicking “Save” saves the browser’s entire current view of the dashboard — not just the new widget. This can overwrite an already-correct Terraform-applied configuration with stale browser state.
If this happens, running terraform apply restores the correct version. The safest practice is to treat any Terraform-managed dashboard as read-only in the console: make all changes in code, then apply.
Also, dashboard widgets can show stale cached data in the browser even after a real config change. A hard refresh (Ctrl+Shift+R) is sometimes needed to see the actual current state.

***

## 7. Escalation

This is a solo project, so there’s no team to page. When something is broken and cannot be resolved through configuration or code changes:

1. Confirm it’s not an IAM/permissions issue by checking whether `AdministratorAccess` should already cover the failing action.

2. If the error message references the **Account** rather than a specific user, role, or resource, it’s likely an account-level AWS restriction. In that case, open an AWS Support case instead of continuing to adjust IAM policies.

3. When opening a case, include:
   - The exact error message.
   - Confirmation that IAM permissions are already sufficient.
   - Any related errors that might share the same root cause.  
   Bundling related issues into one case (as happened here with Glue and Cost Explorer) speeds up diagnosis.