import pulumi
import pulumi_gcp as gcp

_PLACEHOLDER = pulumi.Output.secret("changeme")


def load_config() -> dict:
    config = pulumi.Config()
    return {
        "project": config.get("project") or gcp.config.project,
        "region": config.get("region") or gcp.config.region or "europe-southwest1",
        "scheduler_region": config.get("schedulerRegion") or "europe-west1",
        "db_region": config.get("dbRegion") or config.get("region") or gcp.config.region or "europe-southwest1",
        "service_name": config.get("serviceName") or "bonsai-sensei-api",
        "db_name": config.get("dbName") or "bonsai_db",
        "db_user": config.get("dbUser") or "bonsai_user",
        "db_password": config.require_secret("dbPassword"),
        "image": config.get("image") or "gcr.io/cloudrun/hello",
        "max_instances": config.get_int("maxInstances") or 1,
        "github_owner": config.require("githubOwner"),
        "github_repo": config.get("githubRepo") or "bonsai-sensei",
        "telegram_bot_token": config.get_secret("telegramBotToken") or _PLACEHOLDER,
        "trefle_api_token": config.get_secret("trefleApiToken") or _PLACEHOLDER,
        "tavily_api_key": config.get_secret("tavilyApiKey") or _PLACEHOLDER,
    }
