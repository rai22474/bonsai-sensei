import pulumi_gcp as gcp


def create_service_account() -> gcp.serviceaccount.Account:
    return gcp.serviceaccount.Account(
        "bonsai-sensei-runner",
        account_id="bonsai-sensei-runner",
        display_name="Bonsai Sensei Cloud Run",
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
