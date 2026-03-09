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


def grant_cloudbuild_webhook_secret_accessor(
    project: str,
    webhook_secret: gcp.secretmanager.Secret,
) -> gcp.secretmanager.SecretIamMember:
    project_info = gcp.organizations.get_project(project_id=project)
    cloudbuild_sa = f"serviceAccount:{project_info.number}@cloudbuild.gserviceaccount.com"
    return gcp.secretmanager.SecretIamMember(
        "bonsai-sensei-cloudbuild-webhook-secret-accessor",
        secret_id=webhook_secret.secret_id,
        role="roles/secretmanager.secretAccessor",
        member=cloudbuild_sa,
    )
