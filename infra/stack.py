from apis import enable_apis
from artifact_registry import create_repository
from cloudrun import create_service
from cloudsql import (
    create_database,
    create_database_url,
    create_instance,
    create_user,
)
from config import load_config
from github_actions import (
    create_deployer_service_account,
    create_github_provider,
    create_workload_identity_pool,
    grant_deployer_artifact_registry_writer,
    grant_deployer_run_developer,
    grant_deployer_sa_user_on_runner,
    grant_workload_identity_user,
)
from iam import create_service_account, grant_cloudsql_client, grant_secret_accessor
from network import create_network
from outputs import export_outputs
from secrets import create_database_secret


def build_stack() -> None:
    config = load_config()

    apis = enable_apis(config["project"])

    vpc, subnet = create_network(config["region"], apis)
    repository = create_repository(config["region"], apis)
    instance = create_instance(config["region"], apis)
    create_database(instance, config["db_name"])
    create_user(instance, config["db_user"], config["db_password"])

    service_account = create_service_account(apis)
    grant_cloudsql_client(config["project"], service_account)
    grant_secret_accessor(config["project"], service_account)

    database_url = create_database_url(
        config["db_user"],
        config["db_name"],
        config["db_password"],
        instance,
    )
    secret, _secret_version = create_database_secret(database_url, apis)

    service = create_service(
        config["region"],
        config["service_name"],
        config["image"],
        service_account,
        instance,
        secret,
        config["max_instances"],
        vpc,
        subnet,
    )

    pool = create_workload_identity_pool(apis)
    provider = create_github_provider(pool, config["github_owner"], config["github_repo"])
    deployer_sa = create_deployer_service_account(apis)
    grant_deployer_artifact_registry_writer(config["project"], deployer_sa)
    grant_deployer_run_developer(config["project"], deployer_sa)
    grant_deployer_sa_user_on_runner(service_account, deployer_sa)
    grant_workload_identity_user(pool, deployer_sa, config["github_owner"], config["github_repo"])

    export_outputs(service, instance, repository, secret, provider, deployer_sa)
