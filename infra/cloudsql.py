import pulumi
import pulumi_gcp as gcp


def create_instance(region: str) -> gcp.sql.DatabaseInstance:
    return gcp.sql.DatabaseInstance(
        "bonsai-sensei-db",
        database_version="POSTGRES_15",
        region=region,
        deletion_protection=False,
        settings=gcp.sql.DatabaseInstanceSettingsArgs(
            tier="db-f1-micro",
            disk_size=10,
            disk_type="PD_HDD",
            availability_type="ZONAL",
            activation_policy="ALWAYS",
        ),
    )


def create_database(
    instance: gcp.sql.DatabaseInstance,
    db_name: str,
) -> gcp.sql.Database:
    return gcp.sql.Database(
        "bonsai-sensei-database",
        instance=instance.name,
        name=db_name,
    )


def create_user(
    instance: gcp.sql.DatabaseInstance,
    db_user: str,
    db_password: pulumi.Input[str],
) -> gcp.sql.User:
    return gcp.sql.User(
        "bonsai-sensei-db-user",
        instance=instance.name,
        name=db_user,
        password=db_password,
    )


def create_database_url(
    db_user: str,
    db_name: str,
    db_password: pulumi.Input[str],
    instance: gcp.sql.DatabaseInstance,
) -> pulumi.Output[str]:
    return pulumi.Output.all(db_password, instance.connection_name).apply(
        lambda args: f"postgresql://{db_user}:{args[0]}@/{db_name}?host=/cloudsql/{args[1]}"
    )
