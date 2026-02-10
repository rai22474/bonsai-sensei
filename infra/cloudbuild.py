import pulumi_gcp as gcp


def create_trigger(
    repo_owner: str,
    repo_name: str,
    repo_branch: str,
    build_config_path: str,
    region: str,
    repository_id: str,
    service_name: str,
    pulumi_stack: str,
) -> gcp.cloudbuild.Trigger:
    return gcp.cloudbuild.Trigger(
        "bonsai-sensei-cloudbuild",
        filename=build_config_path,
        github=gcp.cloudbuild.TriggerGithubArgs(
            owner=repo_owner,
            name=repo_name,
            push=gcp.cloudbuild.TriggerGithubPushArgs(
                branch=repo_branch,
            ),
        ),
        substitutions={
            "_REGION": region,
            "_REPOSITORY": repository_id,
            "_SERVICE": service_name,
            "_PULUMI_STACK": pulumi_stack,
        },
    )
