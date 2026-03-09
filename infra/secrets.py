import pulumi
import pulumi_gcp as gcp


def create_webhook_secret(
    webhook_secret_value: pulumi.Input[str],
    api_deps: list | None = None,
) -> tuple[gcp.secretmanager.Secret, gcp.secretmanager.SecretVersion]:
    secret = gcp.secretmanager.Secret(
        "bonsai-sensei-webhook-secret",
        replication=gcp.secretmanager.SecretReplicationArgs(
            auto=gcp.secretmanager.SecretReplicationAutoArgs(),
        ),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )
    secret_version = gcp.secretmanager.SecretVersion(
        "bonsai-sensei-webhook-secret-version",
        secret=secret.id,
        secret_data=webhook_secret_value,
    )
    return secret, secret_version


def create_database_secret(
    database_url: pulumi.Input[str],
    api_deps: list | None = None,
) -> tuple[gcp.secretmanager.Secret, gcp.secretmanager.SecretVersion]:
    secret = gcp.secretmanager.Secret(
        "bonsai-sensei-db-url",
        replication=gcp.secretmanager.SecretReplicationArgs(
            auto=gcp.secretmanager.SecretReplicationAutoArgs(),
        ),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )
    secret_version = gcp.secretmanager.SecretVersion(
        "bonsai-sensei-db-url-version",
        secret=secret.id,
        secret_data=database_url,
    )
    return secret, secret_version
