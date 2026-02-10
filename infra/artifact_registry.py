import pulumi_gcp as gcp


def create_repository(region: str) -> gcp.artifactregistry.Repository:
    return gcp.artifactregistry.Repository(
        "bonsai-sensei-repo",
        format="DOCKER",
        location=region,
        repository_id="bonsai-sensei",
        description="Container images for Bonsai Sensei",
        cleanup_policies=[
            gcp.artifactregistry.RepositoryCleanupPolicyArgs(
                id="keep-three-versions",
                action="KEEP",
                most_recent_versions=gcp.artifactregistry.RepositoryCleanupPolicyMostRecentVersionsArgs(
                    keep_count=3,
                ),
            )
        ],
    )
