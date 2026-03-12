import pulumi_gcp as gcp

REQUIRED_APIS = [
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudscheduler.googleapis.com",
    "monitoring.googleapis.com",
]


def enable_apis(project: str) -> list[gcp.projects.Service]:
    return [
        gcp.projects.Service(
            f"api-{api.replace('.', '-')}",
            project=project,
            service=api,
            disable_on_destroy=False,
        )
        for api in REQUIRED_APIS
    ]
