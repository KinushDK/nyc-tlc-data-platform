# Security Review

## Status

This review was completed by the project author. It has not been independently audited or penetration tested. The goal is to provide an honest assessment of what is secure, what remains a known gap, and what would need to be improved before using the platform in production.

## 1. IAM and Identity

| Item | Status | Notes |
|---|---|---|
| Root account MFA | ✅ Enabled | The root account is used only for account-level settings, such as enabling billing access, and never for daily work. |
| IAM admin user MFA | ✅ Enabled | MFA is enabled for the IAM administrator account. |
| IAM admin permissions | ⚠️ Gap | The user currently has `AdministratorAccess` rather than least-privilege permissions. This was reasonable for a solo development project, but it would need to be restricted in a real team environment. |
| Glue job role (`tlc-platform-glue-job-role`) | ✅ Scoped | S3 permissions are limited to the specific Bronze, Silver, and Gold bucket ARNs rather than `Resource: "*"`. |
| GitHub Actions OIDC role | ✅ Scoped | The trust policy is restricted to the specific repository through the `sub` claim, and permissions are limited to the two ECR repository ARNs. |
| Spark IRSA role (`tlc-platform-spark-irsa-role`) | ⚠️ Partial | The trust policy is correctly restricted to the Kubernetes service account through OIDC. However, the role currently has read and write access across all three S3 buckets instead of being limited by pipeline layer. For example, the Silver job does not need write access to Bronze. |
| EBS CSI driver role | ✅ Scoped | Uses the AWS-managed `AmazonEBSCSIDriverPolicy`, with the trust policy limited to the specific service account in `kube-system`. |

## 2. Network Security

| Item | Status | Notes |
|---|---|---|
| S3 public access | ✅ Blocked | Public access is blocked for the Bronze, Silver, and Gold buckets at the bucket-policy level. |
| EKS API endpoint | ⚠️ Gap | The public endpoint is enabled (`cluster_endpoint_public_access = true`) for development convenience. A production deployment should use a private endpoint or require access through a VPN or bastion host. |
| VPC and subnet design | ✅ Reasonable | Uses the standard EKS module pattern with separate public and private subnets. Worker nodes run in private subnets. |
| Kubernetes NetworkPolicies | ⚠️ Partial | Argo CD's own install manifests create 7 NetworkPolicies restricting traffic to its own components (confirmed via `kubectl get networkpolicy -A`). No NetworkPolicies exist for Airflow, Spark jobs, or the monitoring stack - those namespaces remain open to each other by default. |
| NAT Gateway | ✅ Present | Uses a single NAT Gateway as a cost-saving trade-off instead of deploying one per Availability Zone. |

## 3. Secrets Management

| Item | Status | Notes |
|---|---|---|
| Hardcoded credentials | ✅ None found | AWS access uses IRSA, IAM roles, or GitHub Actions OIDC. No static access keys are stored in the repository. |
| Local development credentials | ⚠️ Acceptable for development | AWS credentials are exported as environment variables for local PySpark testing. This is acceptable on a personal development machine but would not be appropriate for a shared or production environment. |
| Airflow credentials | ⚠️ Gap | Airflow was deployed with the default `admin`/`admin` UI credentials and default Postgres credentials (`postgres`/`postgres`). This is acceptable for a temporary demo cluster but would require proper secrets management for a persistent deployment. |
| Grafana admin password | ⚠️ Minor gap | The password was supplied through a plain `--set grafana.adminPassword=admin` Helm flag, making it visible in shell history and process lists instead of storing it in a Secret. |
| Terraform state | ✅ Secure | Terraform state is stored in a versioned, private S3 bucket with DynamoDB locking. No secrets are committed in the backend configuration. |

## 4. Kubernetes RBAC

| Item | Status | Notes |
|---|---|---|
| Spark job service account (`spark-jobs-sa`) | ✅ Scoped | Uses a namespaced Role limited to the `spark-jobs` namespace. Permissions are restricted to the resources Spark's driver needs: pods, services, ConfigMaps, and PVCs. |
| Airflow worker service account | ✅ Scoped | Uses a namespaced Role that allows management of `SparkApplication` resources, including the `/status` subresource, within `spark-jobs`. |
| Cluster-admin usage | ✅ Avoided | No application workload runs with the actual cluster-admin ClusterRole. Cluster-admin-level access was used only indirectly through the IAM user during setup. |
| Argo CD and Argo Rollouts RBAC | ⚠️ Not reviewed | Both use their own upstream-defined ClusterRoles (confirmed via `kubectl get clusterrole`) to manage resources across namespaces, as their function requires. These are broader than a namespaced Role by necessity, weren't customized for this project, and should be assessed before production use, since ClusterRole-scoped permissions carry more risk than namespaced Roles if either tool were ever compromised. |

## 5. Infrastructure and Terraform

| Item | Status | Notes |
|---|---|---|
| State backend | ✅ Secure | Uses versioned, encrypted, private S3 storage with DynamoDB locking. |
| Secrets in the repository | ✅ Confirmed absent | No `.tfvars` files, access keys, or credentials were found in the project's Git history. |
| Resource tagging and naming | ⚠️ Minimal | Resources are named consistently but do not include cost-centre, owner, or environment tags. This would be a gap in a shared or multi-project AWS account. |
| Terraform version pinning | ✅ Present | Provider versions are pinned through `.terraform.lock.hcl`. |

## 6. Known Gaps and Next Steps

In priority order, I would address the following:

1. **Reduce IAM permissions.** The administrator user is the largest gap. In a real team, broad administrator access should be replaced with role-based permissions tied to specific responsibilities. The Spark IRSA role should also be restricted to only the S3 paths each job requires.
2. **Extend Kubernetes NetworkPolicies beyond Argo CD.** Argo CD already restricts its own traffic by default; Airflow, Spark, and the monitoring stack should get equivalent policies restricting unnecessary cross-namespace access.
3. **Replace default credentials.** Airflow, Postgres, and Grafana should use secrets sourced from AWS Secrets Manager or an appropriate Kubernetes-native solution.
4. **Restrict the EKS API endpoint.** Production access should use a private endpoint, VPN, or bastion host rather than an openly accessible public endpoint.
5. **Review Argo CD and Argo Rollouts ClusterRoles.** Their default permissions should be reviewed against actual usage and tightened where possible before production use.
6. **Add resource tags.** Tags would improve cost allocation, ownership tracking, and future security reviews.

## 7. What Is Already Solid

The project's core trust model is sound. Cross-service integrations — Glue to S3, GitHub Actions to ECR, Spark pods to S3, and the EBS CSI driver to EC2 — use scoped IAM roles with explicit trust conditions through IRSA and OIDC federation.

There are no static credentials in the codebase or CI/CD pipeline. The S3 buckets are locked down, Terraform state is handled securely, and the project's own application workloads (Spark jobs, Airflow's SparkApplication management) use namespaced Kubernetes Roles rather than broad ClusterRoles - the only ClusterRoles present belong to the platform tooling itself (Argo CD, Argo Rollouts), which is expected given how those tools operate.

The remaining gaps are mainly defaults that have not yet been tightened for production, rather than fundamental flaws in the overall design.