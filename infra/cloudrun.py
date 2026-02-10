import pulumi_gcp as gcp


def create_service(
    region: str,
    service_name: str,
    image: str,
    service_account: gcp.serviceaccount.Account,
    instance: gcp.sql.DatabaseInstance,
    secret: gcp.secretmanager.Secret,
    max_instances: int,
) -> gcp.cloudrunv2.Service:
    return gcp.cloudrunv2.Service(
        "bonsai-sensei-service",
        location=region,
        name=service_name,
        ingress="INGRESS_TRAFFIC_ALL",
        template=gcp.cloudrunv2.ServiceTemplateArgs(
            service_account=service_account.email,
            scaling=gcp.cloudrunv2.ServiceTemplateScalingArgs(
                min_instance_count=0,
                max_instance_count=max_instances,
            ),
            volumes=[
                gcp.cloudrunv2.ServiceTemplateVolumeArgs(
                    name="cloudsql",
                    cloud_sql_instance=gcp.cloudrunv2.ServiceTemplateVolumeCloudSqlInstanceArgs(
                        instances=[instance.connection_name],
                    ),
                )
            ],
            containers=[
                gcp.cloudrunv2.ServiceTemplateContainerArgs(
                    image=image,
                    envs=[
                        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="DATABASE_URL",
                            value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret=secret.id,
                                    version="latest",
                                )
                            ),
                        )
                    ],
                    volume_mounts=[
                        gcp.cloudrunv2.ServiceTemplateContainerVolumeMountArgs(
                            name="cloudsql",
                            mount_path="/cloudsql",
                        )
                    ],
                )
            ],
        ),
    )
