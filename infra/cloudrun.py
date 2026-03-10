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
    vpc: gcp.compute.Network,
    subnet: gcp.compute.Subnetwork,
) -> gcp.cloudrunv2.Service:
    return gcp.cloudrunv2.Service(
        "bonsai-sensei-service",
        location=region,
        name=service_name,
        ingress="INGRESS_TRAFFIC_INTERNAL_ONLY",
        template=gcp.cloudrunv2.ServiceTemplateArgs(
            service_account=service_account.email,
            scaling=gcp.cloudrunv2.ServiceTemplateScalingArgs(
                min_instance_count=0,
                max_instance_count=max_instances,
            ),
            vpc_access=gcp.cloudrunv2.ServiceTemplateVpcAccessArgs(
                network_interfaces=[
                    gcp.cloudrunv2.ServiceTemplateVpcAccessNetworkInterfaceArgs(
                        network=vpc.id,
                        subnetwork=subnet.id,
                    )
                ],
                egress="ALL_TRAFFIC",
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
                            value=region,
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
    )
