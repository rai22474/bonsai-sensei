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
        "image": config.require("image"),
        "max_instances": config.get_int("maxInstances") or 1,
        "repo_owner": config.get("repoOwner") or "rai22474",
        "repo_name": config.get("repoName") or "bonsai-sensei",
        "repo_branch": config.get("repoBranch") or "main",
        "build_config_path": config.get("buildConfigPath") or "cloudbuild.yaml",
        "pulumi_stack": config.get("pulumiStack") or "dev",
    }
