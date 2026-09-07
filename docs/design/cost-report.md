# Cost Report v1 — Phase 1 Baseline

## Status
Preliminary — the actual dollar figure is pending due to Cost Explorer’s data lag (see note below). Based on current usage patterns, the total is estimated to be well under $5.


## Summary
| Service                 | Usage                                                                      | Estimated cost impact                                                                |
| ----------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| S3 (Bronze/Silver/Gold) | A few GB of Parquet across 3 buckets                                       | Negligible — S3 storage costs fractions of a cent per GB per month                   |
| AWS Glue                | 3 total job runs (2 Silver, 1 Gold), each a few minutes on 2× G.1X workers | A few cents — Glue bills per DPU-second                                              |
| Step Functions          | 2 executions                                                               | Within the free tier (thousands of free state transitions per month)                 |
| EKS                     | Cluster + NAT gateway ran ~1–2 hours before deliberate teardown            | Small — EKS control plane is $0.10/hr, NAT gateway ~$0.045/hr, both ran only briefly |
| Athena                  | A handful of small queries against Gold Parquet files                      | Negligible — Athena bills per GB scanned, and the Gold marts are tiny                |

## Note on Cost Explorer
When checking Cost Explorer directly on [09/07/2026], it showed $0.00 total cost and a “data unavailable for forecast” message. 
This is consistent with two known AWS behaviors and does not indicate a broken account:

- Cost data has a documented reporting lag of up to ~24 hours after charges occur.
- The account’s usage history (only a few days old at the time of checking) is too short for Cost Explorer’s forecast feature specifically. This is separate from viewing actual historical costs, which should populate once the reporting lag clears.

Plan: Re-check Cost Explorer in 24–48 hours and update this report with the actual figure.

## Cost-control practices used
- Single NAT gateway (not one per Availability Zone) for the EKS VPC, trading some redundancy for lower cost — reasonable for a learning/portfolio project, but would reconsider for production.
- Free-tier-eligible instance types (t3.micro) used for EKS worker nodes, partly due to an account-level restriction on non-Free-Tier instance types at the time.
- EKS cluster and VPC deliberately destroyed between work sessions (terraform destroy -target=module.eks -target=module.vpc) rather than left running idle, since the control plane and NAT gateway are the largest fixed costs regardless of actual workload.
- Small Glue worker counts (2× G.1X) for all jobs — sufficient for the current data volume (single months of one trip type), but will need reassessing once scaling to the full 24–36 month, multi-trip-type range.
- Monthly AWS Budget alert configured early (Phase 0) at 80%/100% thresholds as a safety net against unexpected spend.


## Update log
[09/07/2026]: Initial report written; dollar figure pending due to Cost Explorer lag.