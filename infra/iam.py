import pulumi
import pulumi_gcp as gcp


def create_service_account(api_deps: list | None = None) -> gcp.serviceaccount.Account:
    return gcp.serviceaccount.Account(
        "bonsai-sensei-runner",
        account_id="bonsai-sensei-runner",
        display_name="Bonsai Sensei Cloud Run",
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )


def grant_cloudsql_client(
    project: str,
    service_account: gcp.serviceaccount.Account,
) -> gcp.projects.IAMMember:
    return gcp.projects.IAMMember(
        "bonsai-sensei-cloudsql-client",
        project=project,
        role="roles/cloudsql.client",
        member=service_account.email.apply(lambda email: f"serviceAccount:{email}"),
    )


def grant_secret_accessor(
    project: str,
    service_account: gcp.serviceaccount.Account,
) -> gcp.projects.IAMMember:
    return gcp.projects.IAMMember(
        "bonsai-sensei-secret-accessor",
        project=project,
        role="roles/secretmanager.secretAccessor",
        member=service_account.email.apply(lambda email: f"serviceAccount:{email}"),
    )


def grant_vertex_ai_user(
    project: str,
    service_account: gcp.serviceaccount.Account,
) -> gcp.projects.IAMMember:
    return gcp.projects.IAMMember(
        "bonsai-sensei-vertex-ai-user",
        project=project,
        role="roles/aiplatform.user",
        member=service_account.email.apply(lambda email: f"serviceAccount:{email}"),
    )


def grant_cloud_trace_agent(
    project: str,
    service_account: gcp.serviceaccount.Account,
) -> gcp.projects.IAMMember:
    return gcp.projects.IAMMember(
        "bonsai-sensei-cloud-trace-agent",
        project=project,
        role="roles/cloudtrace.agent",
        member=service_account.email.apply(lambda email: f"serviceAccount:{email}"),
    )


def grant_monitoring_metric_writer(
    project: str,
    service_account: gcp.serviceaccount.Account,
) -> gcp.projects.IAMMember:
    return gcp.projects.IAMMember(
        "bonsai-sensei-monitoring-metric-writer",
        project=project,
        role="roles/monitoring.metricWriter",
        member=service_account.email.apply(lambda email: f"serviceAccount:{email}"),
    )
