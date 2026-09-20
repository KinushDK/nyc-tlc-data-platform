# Cross-Track Comparison: AWS-Native vs Kubernetes-Native

## 1. Summary

Track A and Track B solve the same problem: turning raw NYC TLC trip data into clean, queryable business marts. 
The difference is how they do it.

Track A relies on managed AWS services such as Glue, Step Functions, and Athena. 
Track B runs the same pipeline on Kubernetes using tools such as Spark Operator, Airflow, Argo CD, Argo Rollouts, and Prometheus/Grafana.

In simple terms, Track A reached a reliable working state faster and with fewer moving parts. 
Track B required significantly more debugging, but it demonstrates a broader range of platform-engineering skills. Neither approach is universally better; each suits a different situation, which is the main reason for building both.

## 2. Project Numbers

Across both tracks, between September 1 and September 20, 2026, the project included:

- 125 Git commits.
- 56 merged pull requests.
- Approximately 10 hand-written Terraform files for AWS infrastructure, excluding the 150+ files added automatically through the community EKS and VPC modules.
- 10 Kubernetes, Airflow, and Helm manifest files under `pipelines/orchestration/`.

I didn’t track the hours precisely, but the work took place over several sessions across roughly three weeks. Track B clearly consumed more time than Track A, which is consistent with the difference in the number of issues encountered.

## 3. Issues by Track

The most useful way to compare operational complexity is to look at the number of distinct root causes that had to be identified and fixed, rather than counting repeated attempts at the same problem.

### Track A: approximately 12 issues

Most were isolated problems with relatively straightforward fixes:

- An account-level AWS restriction blocked Glue and Cost Explorer. This was not an IAM problem and required an AWS Support case.
- A Step Functions design issue caused a task’s output to replace its input, so the Gold job did not receive the required arguments. Adding `ResultPath` fixed it.
- CloudWatch custom metrics required an exact match for all dimensions (`Type`, `JobRunId`, and `JobName`), not just `JobName`.
- Editing a Terraform-managed CloudWatch dashboard through the console caused it to revert to stale browser state.
- Local PySpark on Windows required a specific Java version and matching Hadoop-AWS and SDK jar versions before S3 access worked.
- IAM billing access was disabled by default, even for an administrator user.

### Track B: approximately 20 issues

Several of these required multiple attempts to diagnose and resolve:

- The same account-level restriction blocked non-Free-Tier EC2 instance types for EKS nodes.
- `t3.micro` nodes could not run a real Spark workload, even with minimal memory requests.
- It took four attempts to identify the correct Helm value for Spark Operator’s namespace configuration.
- Rebuilding the cluster caused IRSA trust-policy drift because the OIDC provider ID changed each time. There was also a case where Terraform still tracked an IAM role that no longer existed in AWS.
- The Spark driver required Kubernetes RBAC permissions for five different resource types: pods, pod logs, services, ConfigMaps, and PVCs.
- The `apache/spark-py` base image had a reproducible issue where running as the `spark` username could fail because its `/etc/passwd` entry did not always resolve. Running as the numeric UID fixed it.
- Airflow’s Postgres deployment required the EBS CSI driver and a default StorageClass, neither of which exists on a fresh EKS cluster by default.
- Airflow’s `do_xcom_push=True` expected a sidecar container that Spark Operator pods do not provide, causing the task to hang.
- `SparkKubernetesOperator` adds a random suffix to application names by default, so the name did not match what the XCom-free sensor expected.
- The operator deleted the `SparkApplication` immediately after it succeeded, creating a race condition before the sensor could check its status.
- A GitHub Actions OIDC trust policy failed because the token’s actual `sub` claim included numeric account and repository IDs that had not been accounted for. Decoding the real token exposed the issue.
- Two separate node failures caused the kubelet to stop responding, resulting in downstream timeouts that initially looked like application problems.

These issues don’t make Track B a bad choice. Most are common Kubernetes and cloud-native problems that teams eventually encounter in production. The main difference is that Track A abstracts almost all of this operational complexity away, while Track B requires you to manage each layer directly.

## 4. Cost

Track A’s costs closely follow usage. S3 charges for storage, Glue charges for DPU-seconds while jobs run, Step Functions remained within the free tier, and Athena charges per query. When nothing is running, the cost is close to zero.

Track B has fixed costs as soon as the cluster exists, even when no workloads are running. The EKS control plane costs approximately $0.10 per hour (about $73 per month), while a NAT Gateway costs roughly $32 per month. 
Together, they add up to around $100 per month before running a single Spark job.

I ended up destroying and recreating the cluster between work sessions to avoid paying for idle infrastructure. 
That was inconvenient, but it also demonstrated the practical difference between renting managed services as needed and owning infrastructure that must be actively shut down.

## 5. Time to Value

Once IAM access was resolved, a new Glue job in Track A could be written, deployed, and run successfully within minutes.

Track B has a much longer feedback loop. Provisioning a new cluster takes approximately 10–15 minutes, and installing Spark Operator, RBAC, Airflow, Argo CD, and Prometheus adds more time before a test run can even begin.

## 6. Team Size and Skills

Track A is a strong choice for a small team or solo engineer who needs a reliable, low-maintenance pipeline without managing infrastructure. AWS handles much of the patching, scaling, and operational work.

Track B becomes more suitable when an organisation has an existing platform-engineering team or a specific need for Kubernetes. It offers portability, more control, reduced dependence on a single cloud provider, and broadly transferable skills. However, those benefits only justify the additional complexity when the workload or team is large enough to support it.

## 7. What Surprised Me

A few things stood out during the project:

- Most of Track B’s difficulty was in the infrastructure around the data pipeline — RBAC, StorageClasses, OIDC policies, and cluster capacity — rather than in the transformation logic itself.
- A widely used public Docker image can still contain a reproducible bug, as shown by the UID and `/etc/passwd` issue.
- The most effective fixes often came from inspecting the actual evidence: decoding a token, checking the real CloudWatch dimensions, or reading an error message closely.
- Cloud infrastructure can still fail in unexpected ways. Two unrelated node outages in one session were a frustrating reminder that the cloud is ultimately made up of real machines.

## 8. Recommendation

I would generally recommend Track A unless there is a specific reason to choose Kubernetes, such as multi-cloud requirements, an existing Kubernetes platform team, or workloads that genuinely need its portability and control.

The operational cost of Track B is ongoing, not just a one-time setup effort. Even so, the skills demonstrated in Track B are valuable. As platforms grow, managed services may no longer cover every requirement, and teams need engineers who understand what is happening underneath the abstractions.