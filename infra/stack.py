from apis import enable_apis
from artifact_registry import create_repository
from cloudrun import create_migration_job, create_service
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
from iam import (
    create_service_account,
    grant_cloud_trace_agent,
    grant_cloudsql_client,
    grant_monitoring_metric_writer,
    grant_secret_accessor,
    grant_vertex_ai_user,
)
from network import create_network, create_private_google_access, create_vpc_connector
from outputs import export_outputs
from monitoring import create_dashboard
from scheduler import create_cloudrun_schedule, create_db_schedule
from secrets import create_database_secret, create_telegram_secret, create_trefle_secret, create_tavily_secret


def build_stack() -> None:
    config = load_config()

    apis = enable_apis(config["project"])

    vpc, subnet = create_network(config["region"], apis)
    create_private_google_access(vpc, apis)
    connector = create_vpc_connector(config["region"], vpc, apis)
    repository = create_repository(config["region"], apis)
    instance = create_instance(config["db_region"], apis)
    create_database(instance, config["db_name"])
    create_user(instance, config["db_user"], config["db_password"])

    service_account = create_service_account(apis)
    grant_cloudsql_client(config["project"], service_account)
    grant_secret_accessor(config["project"], service_account)
    grant_vertex_ai_user(config["project"], service_account)
    grant_cloud_trace_agent(config["project"], service_account)
    grant_monitoring_metric_writer(config["project"], service_account)

    database_url = create_database_url(
        config["db_user"],
        config["db_name"],
        config["db_password"],
        instance,
    )
    database_secret, database_secret_version = create_database_secret(database_url, apis)
    telegram_secret, telegram_secret_version = create_telegram_secret(config["telegram_bot_token"], apis)
    trefle_secret, trefle_secret_version = create_trefle_secret(config["trefle_api_token"], apis)
    tavily_secret, tavily_secret_version = create_tavily_secret(config["tavily_api_key"], apis)

    secret_versions = [database_secret_version, telegram_secret_version, trefle_secret_version, tavily_secret_version]

    service = create_service(
        config["region"],
        config["project"],
        config["service_name"],
        config["image"],
        service_account,
        instance,
        database_secret,
        telegram_secret,
        trefle_secret,
        tavily_secret,
        config["max_instances"],
        connector,
        secret_versions,
    )

    migration_job = create_migration_job(
        config["region"],
        config["image"],
        service_account,
        instance,
        database_secret,
        connector,
        [*apis, *secret_versions],
    )

    create_db_schedule(config["project"], config["scheduler_region"], instance, apis)
    create_cloudrun_schedule(config["project"], config["scheduler_region"], service, service_account, apis)
    create_dashboard(apis)

    pool = create_workload_identity_pool(apis)
    provider = create_github_provider(pool, config["github_owner"], config["github_repo"])
    deployer_sa = create_deployer_service_account(apis)
    grant_deployer_artifact_registry_writer(config["project"], deployer_sa)
    grant_deployer_run_developer(config["project"], deployer_sa)
    grant_deployer_sa_user_on_runner(service_account, deployer_sa)
    grant_workload_identity_user(pool, deployer_sa, config["github_owner"], config["github_repo"])

    export_outputs(service, migration_job, instance, repository, database_secret, provider, deployer_sa)
