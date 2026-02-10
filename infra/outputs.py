import pulumi
import pulumi_gcp as gcp


def export_outputs(
    service: gcp.cloudrunv2.Service,
    instance: gcp.sql.DatabaseInstance,
    repository: gcp.artifactregistry.Repository,
    secret: gcp.secretmanager.Secret,
) -> None:
    pulumi.export("service_url", service.uri)
    pulumi.export("database_connection_name", instance.connection_name)
    pulumi.export("artifact_registry", repository.repository_id)
    pulumi.export("secret_name", secret.secret_id)
