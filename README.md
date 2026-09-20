# NYC TLC Data Platform

A production-style data platform built on NYC Taxi & Limousine Commission trip data, implemented **twice** — once on fully managed AWS services
(Track A) and once on Kubernetes with a self-managed, open-source stack
(Track B) — to genuinely compare the two approaches rather than just read about the tradeoffs.

**Repo:** https://github.com/KinushDK/nyc-tlc-data-platform

## What this actually is

Raw NYC Yellow Taxi trip data gets cleaned, validated, and turned into queryable business marts (daily trip volume by borough, fare/tip
trends) through a Bronze → Silver → Gold medallion pipeline. 
Both tracks do the exact same transformation logic — same PySpark code, same input, same output — but everything around that logic (compute, orchestration, deployment, observability) is built completely differently between the two.

## Track A: AWS-Native

- **Storage:** S3 (Bronze/Silver/Gold), versioned, public access blocked
- **Compute:** AWS Glue (Spark, managed)
- **Orchestration:** Step Functions
- **Query:** Athena, with tables registered in the Glue Data Catalog
- **Observability:** CloudWatch dashboard
- **Infra as code:** Terraform

## Track B: Kubernetes-Native

- **Compute:** Containerized PySpark, run via Spark Operator on EKS
- **Orchestration:** Apache Airflow (`KubernetesExecutor`)
- **CI/CD:** GitHub Actions → ECR, authenticated via OIDC (no static AWS keys)
- **GitOps:** Argo CD, self-healing proven against manual drift
- **Progressive delivery:** Argo Rollouts (canary deployment, live traffic-split verified)
- **Observability:** Prometheus + Grafana
- **Infra as code:** Terraform (EKS/VPC), Helm + Kubernetes manifests (everything running on the cluster)

## Why build it twice

Because "which is better, managed services or Kubernetes" is a question people argue about constantly, usually without having actually built
the same thing both ways. So I did. The full comparison — real cost numbers, real bugs hit and fixed on each side, an honest recommendation
— is in [`docs/design/cross-track-comparison.md`](docs/design/cross-track-comparison.md).

Short version: Track A got to a working, reliable pipeline faster and cheaper. 
Track B took a lot more debugging, but the end result demonstrates a much broader set of platform engineering skills. 
Neither one is the "right" answer in general — they're right for different situations.

## Project docs

Everything below reflects real decisions and real problems hit while building this, not a polished-after-the-fact writeup:

- [`docs/adr/`](docs/adr/) 
  — Architecture Decision Records, written before implementation, documenting why each major technical choice was made
- [`docs/design/system-design.md`](docs/design/system-design.md) 
  — how the whole system fits together, with an architecture diagram
- [`docs/design/runbook.md`](docs/design/runbook.md) 
  — how to deploy, operate, and recover this platform, including a genuinely long list of real gotchas hit during development (Kubernetes RBAC quirks, a base Docker image bug, cluster nodes going unresponsive mid-session, and more)
- [`docs/design/data-observations.md`](docs/design/data-observations.md)
  — what's actually in the raw data, including a root-cause investigation into a pattern of missing fields that turned out to trace back to a specific `payment_type` value
- [`docs/design/cross-track-comparison.md`](docs/design/cross-track-comparison.md)
  — Track A vs Track B, with real numbers
- [`docs/design/performance-benchmarks.md`](docs/design/performance-benchmarks.md)
  — actual measured job execution times on both tracks
- [`docs/design/security-review.md`](docs/design/security-review.md)
  — a self-reviewed, honest checklist of what's secure, what's a known gap, and what I'd fix with more time
- [`docs/design/cost-report.md`](docs/design/cost-report.md) 
  — what this actually cost to build and run

## Repo layout