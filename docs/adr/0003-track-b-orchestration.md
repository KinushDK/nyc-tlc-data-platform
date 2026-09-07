# ADR-0003: Track B Orchestration and Compute — Airflow + Spark Operator

## Status
Accepted

## Context

Track A already demonstrates AWS-managed orchestration and compute: 
Glue for Spark jobs and Step Functions for sequencing them.

Track B is meant to show the other side of the same problem — running the same Bronze → Silver → Gold logic on Kubernetes, with more infrastructure ownership and less reliance on managed AWS services.

This means two separate decisions for Track B:
- What runs the Spark transformation jobs on Kubernetes.
- What orchestrates and sequences those jobs.

The two realistic options were:
- Use Spark Operator alone, letting it handle both running the jobs and their sequencing via dependencies.
- Add Airflow on top as a dedicated orchestrator, with Spark Operator underneath actually executing the Spark workloads.

## Decision

**Chosen:** Airflow, running on the EKS cluster via the Kubernetes Executor, orchestrating jobs that Spark Operator executes.

**Reasons:**
- Airflow is one of the most frequently requested tools in Data Engineering job postings, giving it broader market relevance than Spark Operator alone.
- Running Airflow itself on Kubernetes is real platform-engineering experience (webserver, scheduler, KubernetesExecutor pods). It’s not just “write a DAG,” but actually operating the orchestration layer.
- Having both Step Functions (Track A) and Airflow (Track B) built gives a genuine basis for comparing the two orchestration paradigms in the cross-track comparison doc, rather than comparing on assumptions.

## Alternatives Considered

**Spark Operator only, no separate orchestrator**  
Spark Operator can handle simple sequencing on its own (for example, via dependencies between `SparkApplication` resources or a lightweight wrapper). This would have been a smaller, faster-to-finish scope — essentially just containerizing the existing PySpark logic and running it natively on Kubernetes.

It wasn’t chosen because it would leave Track B without its own orchestration story, and orchestration is one of the most commonly evaluated skills in Data Engineering roles. Given the project’s goal of building breadth across tools relevant to the job market, skipping Airflow would have left a gap that Spark Operator alone doesn’t fill.

## Consequences

- Track B’s scope is meaningfully larger than “Spark Operator only.” Deploying and operating Airflow is real infrastructure work in addition to the Spark jobs themselves.
- There is a real risk that this could extend Track B’s timeline well beyond the original estimate. It’s worth monitoring progress against the plan and being willing to cut scope (for example, skip Airflow features like backfills, SLAs, or complex branching DAGs) if time pressure builds. A working simple DAG is better than an unfinished sophisticated one.
- All Track B job sequencing will go through Airflow DAGs from this point forward. Spark Operator’s role is strictly to run the Spark workloads it’s told to run, not to decide when.
- This decision assumes that running Airflow on Kubernetes is achievable within the project’s realistic time budget. If it proves too heavy, this ADR should be revisited rather than silently abandoned.