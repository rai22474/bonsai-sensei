import pulumi
import pulumi_gcp as gcp


def export_outputs(
    service: gcp.cloudrunv2.Service,
    migration_job: gcp.cloudrunv2.Job,
    instance: gcp.sql.DatabaseInstance,
    repository: gcp.artifactregistry.Repository,
    secret: gcp.secretmanager.Secret,
    wif_provider: gcp.iam.WorkloadIdentityPoolProvider,
    deployer_sa: gcp.serviceaccount.Account,
) -> None:
    pulumi.export("service_url", service.uri)
    pulumi.export("migration_job_name", migration_job.name)
    pulumi.export("database_connection_name", instance.connection_name)
    pulumi.export("artifact_registry", repository.repository_id)
    pulumi.export("secret_name", secret.secret_id)
    pulumi.export("wif_provider", wif_provider.name)
    pulumi.export("deployer_sa_email", deployer_sa.email)
