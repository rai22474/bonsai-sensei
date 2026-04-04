import pulumi
import pulumi_gcp as gcp


def create_workload_identity_pool(api_deps: list | None = None) -> gcp.iam.WorkloadIdentityPool:
    return gcp.iam.WorkloadIdentityPool(
        "github-pool",
        workload_identity_pool_id="github-pool",
        display_name="GitHub Actions Pool",
        opts=pulumi.ResourceOptions(depends_on=api_deps or [], retain_on_delete=True),
    )


def create_github_provider(
    pool: gcp.iam.WorkloadIdentityPool,
    github_owner: str,
    github_repo: str,
) -> gcp.iam.WorkloadIdentityPoolProvider:
    return gcp.iam.WorkloadIdentityPoolProvider(
        "github-provider",
        workload_identity_pool_id=pool.workload_identity_pool_id,
        workload_identity_pool_provider_id="github-provider",
        display_name="GitHub Actions Provider",
        oidc=gcp.iam.WorkloadIdentityPoolProviderOidcArgs(
            issuer_uri="https://token.actions.githubusercontent.com",
        ),
        attribute_mapping={
            "google.subject": "assertion.sub",
            "attribute.actor": "assertion.actor",
            "attribute.repository": "assertion.repository",
        },
        attribute_condition=f'attribute.repository == "{github_owner}/{github_repo}"',
        opts=pulumi.ResourceOptions(retain_on_delete=True),
    )


def create_deployer_service_account(api_deps: list | None = None) -> gcp.serviceaccount.Account:
    return gcp.serviceaccount.Account(
        "github-actions-deployer",
        account_id="github-actions-deployer",
        display_name="GitHub Actions Deployer",
        opts=pulumi.ResourceOptions(depends_on=api_deps or [], retain_on_delete=True),
    )


def grant_deployer_artifact_registry_writer(
    project: str,
    deployer_sa: gcp.serviceaccount.Account,
) -> gcp.projects.IAMMember:
    return gcp.projects.IAMMember(
        "github-actions-artifact-registry-writer",
        project=project,
        role="roles/artifactregistry.writer",
        member=deployer_sa.email.apply(lambda email: f"serviceAccount:{email}"),
    )


def grant_deployer_run_developer(
    project: str,
    deployer_sa: gcp.serviceaccount.Account,
) -> gcp.projects.IAMMember:
    return gcp.projects.IAMMember(
        "github-actions-run-developer",
        project=project,
        role="roles/run.developer",
        member=deployer_sa.email.apply(lambda email: f"serviceAccount:{email}"),
    )


def grant_deployer_sa_user_on_runner(
    runner_sa: gcp.serviceaccount.Account,
    deployer_sa: gcp.serviceaccount.Account,
) -> gcp.serviceaccount.IAMMember:
    return gcp.serviceaccount.IAMMember(
        "github-actions-sa-user",
        service_account_id=runner_sa.name,
        role="roles/iam.serviceAccountUser",
        member=deployer_sa.email.apply(lambda email: f"serviceAccount:{email}"),
    )


def grant_workload_identity_user(
    pool: gcp.iam.WorkloadIdentityPool,
    deployer_sa: gcp.serviceaccount.Account,
    github_owner: str,
    github_repo: str,
) -> gcp.serviceaccount.IAMMember:
    principal = pool.name.apply(
        lambda pool_name: f"principalSet://iam.googleapis.com/{pool_name}/attribute.repository/{github_owner}/{github_repo}"
    )
    return gcp.serviceaccount.IAMMember(
        "github-actions-wif-binding",
        service_account_id=deployer_sa.name,
        role="roles/iam.workloadIdentityUser",
        member=principal,
    )
