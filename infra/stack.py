from infra.artifact_registry import create_repository
from infra.cloudbuild import create_trigger
from infra.cloudrun import create_service
from infra.cloudsql import (
    create_database,
    create_database_url,
    create_instance,
    create_user,
)
from infra.config import load_config
from infra.iam import create_service_account, grant_cloudsql_client, grant_secret_accessor
from infra.outputs import export_outputs
from infra.secrets import create_database_secret


def build_stack() -> None:
    config = load_config()

    repository = create_repository(config["region"])
    instance = create_instance(config["region"])
    create_database(instance, config["db_name"])
    create_user(instance, config["db_user"], config["db_password"])

    create_trigger(
        config["repo_owner"],
        config["repo_name"],
        config["repo_branch"],
        config["build_config_path"],
        config["region"],
        repository.repository_id,
        config["service_name"],
        config["pulumi_stack"],
    )

    service_account = create_service_account()
    grant_cloudsql_client(config["project"], service_account)
    grant_secret_accessor(config["project"], service_account)

    database_url = create_database_url(
        config["db_user"],
        config["db_name"],
        config["db_password"],
        instance,
    )
    secret, _secret_version = create_database_secret(database_url)

    service = create_service(
        config["region"],
        config["service_name"],
        config["image"],
        service_account,
        instance,
        secret,
        config["max_instances"],
    )

    export_outputs(service, instance, repository, secret)
