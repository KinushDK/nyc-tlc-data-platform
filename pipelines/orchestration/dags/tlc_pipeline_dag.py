from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import (
    SparkKubernetesOperator,
)
from airflow.providers.cncf.kubernetes.sensors.spark_kubernetes import (
    SparkKubernetesSensor,
)

default_args = {
    "owner": "tlc-platform",
    "retries": 2,
    "retry_delay": timedelta(seconds=30),
}

with DAG(
    dag_id="tlc_silver_gold_pipeline",
    default_args=default_args,
    schedule=None,
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    tags=["tlc", "spark", "silver-gold"],
) as dag:
    submit_silver = SparkKubernetesOperator(
        task_id="submit_silver_transform",
        namespace="spark-jobs",
        application_file="silver-spark-application.yaml",
        kubernetes_conn_id="kubernetes_default",
        do_xcom_push=False,
    )

    monitor_silver = SparkKubernetesSensor(
        task_id="monitor_silver_transform",
        namespace="spark-jobs",
        application_name="silver-yellow-transform",
        kubernetes_conn_id="kubernetes_default",
    )

    submit_gold = SparkKubernetesOperator(
        task_id="submit_gold_transform",
        namespace="spark-jobs",
        application_file="gold-spark-application.yaml",
        kubernetes_conn_id="kubernetes_default",
        do_xcom_push=False,
    )

    monitor_gold = SparkKubernetesSensor(
        task_id="monitor_gold_transform",
        namespace="spark-jobs",
        application_name="gold-yellow-marts",
        kubernetes_conn_id="kubernetes_default",
    )

    submit_silver >> monitor_silver >> submit_gold >> monitor_gold
