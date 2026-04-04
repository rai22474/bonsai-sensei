import pulumi
import pulumi_gcp as gcp


def create_service(
    region: str,
    project: str,
    service_name: str,
    image: str,
    service_account: gcp.serviceaccount.Account,
    instance: gcp.sql.DatabaseInstance,
    database_secret: gcp.secretmanager.Secret,
    telegram_secret: gcp.secretmanager.Secret,
    trefle_secret: gcp.secretmanager.Secret,
    tavily_secret: gcp.secretmanager.Secret,
    max_instances: int,
    connector: gcp.vpcaccess.Connector,
    secret_deps: list | None = None,
    vertex_location: str = "europe-west1",
) -> gcp.cloudrunv2.Service:
    return gcp.cloudrunv2.Service(
        "bonsai-sensei-service",
        location=region,
        name=service_name,
        deletion_protection=False,
        ingress="INGRESS_TRAFFIC_INTERNAL_ONLY",
        template=gcp.cloudrunv2.ServiceTemplateArgs(
            service_account=service_account.email,
            scaling=gcp.cloudrunv2.ServiceTemplateScalingArgs(
                min_instance_count=1,
                max_instance_count=max_instances,
            ),
            vpc_access=gcp.cloudrunv2.ServiceTemplateVpcAccessArgs(
                connector=connector.id,
                egress="PRIVATE_RANGES_ONLY",
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
                                    secret=database_secret.id,
                                    version="latest",
                                )
                            ),
                        ),
                        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="TELEGRAM_BOT_TOKEN",
                            value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret=telegram_secret.id,
                                    version="latest",
                                )
                            ),
                        ),
                        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="TREFLE_API_TOKEN",
                            value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret=trefle_secret.id,
                                    version="latest",
                                )
                            ),
                        ),
                        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="TAVILY_API_KEY",
                            value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret=tavily_secret.id,
                                    version="latest",
                                )
                            ),
                        ),
                        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="GOOGLE_GENAI_USE_VERTEXAI",
                            value="true",
                        ),
                        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="GOOGLE_CLOUD_PROJECT",
                            value=project,
                        ),
                        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="GOOGLE_CLOUD_LOCATION",
                            value="europe-west1",
                        ),
                        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="OTEL_SERVICE_NAME",
                            value=service_name,
                        ),
                        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="DEPLOYMENT_ENV",
                            value="production",
                        ),
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
        opts=pulumi.ResourceOptions(
            depends_on=secret_deps or [],
            ignore_changes=["template.scaling.minInstanceCount"],
            delete_before_replace=True,
        ),
    )


def create_migration_job(
    region: str,
    image: str,
    service_account: gcp.serviceaccount.Account,
    instance: gcp.sql.DatabaseInstance,
    database_secret: gcp.secretmanager.Secret,
    connector: gcp.vpcaccess.Connector,
    api_deps: list | None = None,
) -> gcp.cloudrunv2.Job:
    return gcp.cloudrunv2.Job(
        "bonsai-sensei-migrate",
        location=region,
        name="bonsai-sensei-migrate",
        deletion_protection=False,
        template=gcp.cloudrunv2.JobTemplateArgs(
            template=gcp.cloudrunv2.JobTemplateTemplateArgs(
                service_account=service_account.email,
                max_retries=0,
                vpc_access=gcp.cloudrunv2.JobTemplateTemplateVpcAccessArgs(
                    connector=connector.id,
                    egress="PRIVATE_RANGES_ONLY",
                ),
                volumes=[
                    gcp.cloudrunv2.JobTemplateTemplateVolumeArgs(
                        name="cloudsql",
                        cloud_sql_instance=gcp.cloudrunv2.JobTemplateTemplateVolumeCloudSqlInstanceArgs(
                            instances=[instance.connection_name],
                        ),
                    )
                ],
                containers=[
                    gcp.cloudrunv2.JobTemplateTemplateContainerArgs(
                        image=image,
                        commands=["python"],
                        args=["init_db.py"],
                        envs=[
                            gcp.cloudrunv2.JobTemplateTemplateContainerEnvArgs(
                                name="DATABASE_URL",
                                value_source=gcp.cloudrunv2.JobTemplateTemplateContainerEnvValueSourceArgs(
                                    secret_key_ref=gcp.cloudrunv2.JobTemplateTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                        secret=database_secret.id,
                                        version="latest",
                                    )
                                ),
                            ),
                        ],
                        volume_mounts=[
                            gcp.cloudrunv2.JobTemplateTemplateContainerVolumeMountArgs(
                                name="cloudsql",
                                mount_path="/cloudsql",
                            )
                        ],
                    )
                ],
            )
        ),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )
