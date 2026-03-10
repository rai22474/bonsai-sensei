import pulumi
import pulumi_gcp as gcp


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


def create_telegram_secret(
    token: pulumi.Input[str],
    api_deps: list | None = None,
) -> tuple[gcp.secretmanager.Secret, gcp.secretmanager.SecretVersion]:
    secret = gcp.secretmanager.Secret(
        "bonsai-sensei-telegram-token",
        replication=gcp.secretmanager.SecretReplicationArgs(
            auto=gcp.secretmanager.SecretReplicationAutoArgs(),
        ),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )
    secret_version = gcp.secretmanager.SecretVersion(
        "bonsai-sensei-telegram-token-version",
        secret=secret.id,
        secret_data=token,
    )
    return secret, secret_version


def create_trefle_secret(
    token: pulumi.Input[str],
    api_deps: list | None = None,
) -> tuple[gcp.secretmanager.Secret, gcp.secretmanager.SecretVersion]:
    secret = gcp.secretmanager.Secret(
        "bonsai-sensei-trefle-token",
        replication=gcp.secretmanager.SecretReplicationArgs(
            auto=gcp.secretmanager.SecretReplicationAutoArgs(),
        ),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )
    secret_version = gcp.secretmanager.SecretVersion(
        "bonsai-sensei-trefle-token-version",
        secret=secret.id,
        secret_data=token,
    )
    return secret, secret_version


def create_tavily_secret(
    api_key: pulumi.Input[str],
    api_deps: list | None = None,
) -> tuple[gcp.secretmanager.Secret, gcp.secretmanager.SecretVersion]:
    secret = gcp.secretmanager.Secret(
        "bonsai-sensei-tavily-key",
        replication=gcp.secretmanager.SecretReplicationArgs(
            auto=gcp.secretmanager.SecretReplicationAutoArgs(),
        ),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )
    secret_version = gcp.secretmanager.SecretVersion(
        "bonsai-sensei-tavily-key-version",
        secret=secret.id,
        secret_data=api_key,
    )
    return secret, secret_version
