# Performance Benchmarks

## Test conditions
- Dataset: NYC Yellow Taxi, March 2025 (4,145,253 rows post-Silver-cleaning)
- Track A: AWS Glue, 2x G.1X workers (Glue version 4.0)
- Track B: Spark Operator on EKS, t3.small nodes, 512m driver/executor memory

## Raw job execution times

| Job | Track A (Glue) | Track B (Spark on K8s) |
|---|---|---|
| Silver transform | 149s, 112s, 158s (avg ~140s) | 151s |
| Gold marts | 96s, 90s (avg ~93s) | 64s |

## Full orchestrated pipeline (Silver -> Gold, including orchestration overhead)

| | Track A (Step Functions) | Track B (Airflow) |
|---|---|---|
| Total duration | ~4-5 min (estimated from individual job times plus Step Functions overhead - not measured directly) | 5:44 (measured directly from a successful DAG run) |

## Observations

The two engines perform almost identically on the same data, which
isn't surprising - it's the same PySpark logic running either way, on
roughly comparable worker specs. The real performance story in this
project was never about compute speed; it was about orchestration
overhead and, especially for Track B, about how much work it took to
get to a working state in the first place.

A few honest caveats: these numbers come from single or few-run
measurements on one month of data, not a rigorous repeated-trial
benchmark. Track B's numbers also reflect deliberately undersized nodes
(t3.small, chosen due to an account-level Free Tier restriction) rather
than production-equivalent hardware, so the comparison understates how
Track B would perform with properly sized infrastructure.