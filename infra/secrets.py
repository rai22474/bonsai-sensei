import pulumi
import pulumi_gcp as gcp


def create_database_secret(
    database_url: pulumi.Input[str],
) -> tuple[gcp.secretmanager.Secret, gcp.secretmanager.SecretVersion]:
    secret = gcp.secretmanager.Secret(
        "bonsai-sensei-db-url",
        replication=gcp.secretmanager.SecretReplicationArgs(
            automatic=True,
        ),
    )
    secret_version = gcp.secretmanager.SecretVersion(
        "bonsai-sensei-db-url-version",
        secret=secret.id,
        secret_data=database_url,
    )
    return secret, secret_version
