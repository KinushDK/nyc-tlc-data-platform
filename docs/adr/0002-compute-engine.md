# ADR-0002: Compute Engine for Bronze → Silver → Gold Transformations

## Status
Accepted

## Context
Now that the raw Yellow Taxi data is landing in the Bronze S3 bucket, the next step is to handle the actual transformation logic: cleaning and validating records for the Silver layer, 
and then building business-ready tables for the Gold layer. This work needs to run on a distributed compute engine, since even a single month of data already contains 3–4 million rows, 
and the full project scope (24–36 months across three trip types) will be much larger.

AWS offers two realistic serverless options for running Spark without having to manage a cluster yourself: AWS Glue and EMR Serverless. 
Both avoid the overhead of provisioning and maintaining EC2-based clusters, which is important for a solo project where time is the most limited resource. 
The real decision comes down to which option fits better with the rest of Track A, rather than which one is more powerful in general.

## Decision
Chosen: AWS Glue, for both the Silver and Gold transformation jobs in
Track A.

The main reasons for this choice are:
- Glue’s Data Catalog integrates directly with Athena, so tables written to the Gold layer are immediately queryable without needing a separate cataloging step.
- Glue Job Bookmarks provide built-in tracking of which files or partitions have already been processed. This aligns well with the project’s need for idempotency — re-running a job shouldn’t reprocess or duplicate data.
- Glue is more commonly expected in AWS-native Data Engineer job postings, so gaining fluency with it has direct value beyond this project.
- It keeps Track A’s toolchain fully AWS-native (S3, Glue, Athena, Step Functions), which is the whole point of having two distinct tracks — Track B will cover the more infrastructure-heavy, Kubernetes-based version of the same problem.

## Alternatives Considered

**EMR Serverless**
EMR Serverless gives more direct control over the underlying Spark environment — you can choose Spark versions, fine-tune configurations more precisely, and it behaves closer to open-source Spark rather than a managed AWS abstraction. 
It’s also billed serverlessly, so there’s no significant cost difference at this project’s scale.

It wasn’t chosen for Track A because it doesn’t include the Data Catalog or job bookmarking out of the box — both would need to be built manually, which adds work without providing skills that Glue doesn’t already cover for this use case. 
Since Track B’s Kubernetes-based pipeline will already use the Spark Operator (which is much closer to raw Spark), choosing Glue here also means the project demonstrates a wider range of tools instead of doing “managed Spark” twice in two different tracks.

## Consequences
- Silver and Gold jobs will be written as Glue ETL jobs (PySpark scripts running on Glue’s managed Spark runtime), so they won’t be directly portable to EMR without some rework.
- Idempotency for Bronze → Silver → Gold runs will rely on Glue Job Bookmarks rather than a custom-built tracking mechanism. This needs to be validated early, since bookmarks have their own behaviors and limitations that should be tested rather than assumed.
- There will be less low-level control over Spark tuning compared to EMR Serverless — acceptable at this data volume, but worth revisiting if performance becomes a real constraint later in the project.
- All future Track A ADRs and design documents should assume Glue as the compute layer unless explicitly revisited.
- This ADR is written before any Glue job has actually been implemented — if bookmarks or the Glue job model turn out to have unexpected limitations once the Silver layer is built, that's a legitimate reason to revisit this decision, not a failure of the ADR process.