import pulumi
import pulumi_gcp as gcp


def load_config() -> dict:
    config = pulumi.Config()
    return {
        "project": config.get("project") or gcp.config.project,
        "region": config.get("region") or gcp.config.region or "europe-west1",
        "service_name": config.get("serviceName") or "bonsai-sensei-api",
        "db_name": config.get("dbName") or "bonsai_db",
        "db_user": config.get("dbUser") or "bonsai_user",
        "db_password": config.require_secret("dbPassword"),
        "image": config.get("image") or "gcr.io/cloudrun/hello",
        "max_instances": config.get_int("maxInstances") or 1,
        "github_owner": config.require("githubOwner"),
        "github_repo": config.get("githubRepo") or "bonsai-sensei",
    }
