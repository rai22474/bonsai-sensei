import pulumi
import pulumi_gcp as gcp


def create_trigger(
    project: str,
    repo_owner: str,
    repo_name: str,
    repo_branch: str,
    region: str,
    repository_id: str,
    service_name: str,
    pulumi_stack: str,
    webhook_secret_version: gcp.secretmanager.SecretVersion,
    api_deps: list | None = None,
) -> gcp.cloudbuild.Trigger:
    image_uri = f"{region}-docker.pkg.dev/$PROJECT_ID/{repository_id}/bonsai-sensei:$_COMMIT_SHA"
    return gcp.cloudbuild.Trigger(
        "bonsai-sensei-cloudbuild",
        project=project,
        webhook_config=gcp.cloudbuild.TriggerWebhookConfigArgs(
            secret=webhook_secret_version.id,
        ),
        filter=f'body.ref == "refs/heads/{repo_branch}"',
        substitutions={
            "_REGION": region,
            "_REPOSITORY": repository_id,
            "_SERVICE": service_name,
            "_PULUMI_STACK": pulumi_stack,
            "_COMMIT_SHA": "$(body.after)",
        },
        build=gcp.cloudbuild.TriggerBuildArgs(
            steps=[
                gcp.cloudbuild.TriggerBuildStepArgs(
                    id="Clone",
                    name="gcr.io/cloud-builders/git",
                    args=["clone", f"https://github.com/{repo_owner}/{repo_name}.git", "--branch", f"{repo_branch}", "--single-branch", "."],
                ),
                gcp.cloudbuild.TriggerBuildStepArgs(
                    id="Checkout commit",
                    name="gcr.io/cloud-builders/git",
                    args=["checkout", "$_COMMIT_SHA"],
                ),
                gcp.cloudbuild.TriggerBuildStepArgs(
                    id="Build image",
                    name="gcr.io/cloud-builders/docker",
                    args=["build", "-t", image_uri, "."],
                ),
                gcp.cloudbuild.TriggerBuildStepArgs(
                    id="Push image",
                    name="gcr.io/cloud-builders/docker",
                    args=["push", image_uri],
                ),
                gcp.cloudbuild.TriggerBuildStepArgs(
                    id="Pulumi up",
                    name="pulumi/pulumi-python",
                    entrypoint="bash",
                    secret_envs=["PULUMI_ACCESS_TOKEN"],
                    args=[
                        "-c",
                        f"cd infra && pip install . && pulumi stack select ${{_PULUMI_STACK}} && pulumi config set project $PROJECT_ID && pulumi config set region ${{_REGION}} && pulumi config set serviceName ${{_SERVICE}} && pulumi config set image {image_uri} && pulumi up --yes",
                    ],
                ),
            ],
            available_secrets=gcp.cloudbuild.TriggerBuildAvailableSecretsArgs(
                secret_managers=[
                    gcp.cloudbuild.TriggerBuildAvailableSecretsSecretManagerArgs(
                        env="PULUMI_ACCESS_TOKEN",
                        version_name=f"projects/{project}/secrets/pulumi-access-token/versions/latest",
                    ),
                ],
            ),
        ),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )
