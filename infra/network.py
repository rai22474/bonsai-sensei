import pulumi
import pulumi_gcp as gcp


def create_network(
    region: str,
    api_deps: list | None = None,
) -> tuple[gcp.compute.Network, gcp.compute.Subnetwork]:
    vpc = gcp.compute.Network(
        "bonsai-sensei-vpc",
        name="bonsai-sensei-vpc",
        auto_create_subnetworks=False,
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )

    subnet = gcp.compute.Subnetwork(
        "bonsai-sensei-subnet",
        name="bonsai-sensei-subnet",
        region=region,
        network=vpc.id,
        ip_cidr_range="10.8.0.0/24",
        private_ip_google_access=True,
        opts=pulumi.ResourceOptions(delete_before_replace=True),
    )

    return vpc, subnet


def create_vpc_connector(
    region: str,
    vpc: gcp.compute.Network,
    api_deps: list | None = None,
) -> gcp.vpcaccess.Connector:
    return gcp.vpcaccess.Connector(
        "bonsai-sensei-connector",
        name="bonsai-connector",
        region=region,
        network=vpc.id,
        ip_cidr_range="10.8.1.0/28",
        min_instances=2,
        max_instances=3,
        machine_type="e2-micro",
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )


def create_private_google_access(
    vpc: gcp.compute.Network,
    api_deps: list | None = None,
) -> None:
    psc_address = gcp.compute.GlobalAddress(
        "bonsai-sensei-psc-apis",
        name="bonsai-sensei-psc-apis",
        address_type="INTERNAL",
        purpose="PRIVATE_SERVICE_CONNECT",
        network=vpc.id,
        address="10.100.0.2",
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )

    gcp.compute.GlobalForwardingRule(
        "bonsai-sensei-psc-apis-fwd",
        name="bonsaipscfwd",
        target="all-apis",
        network=vpc.id,
        ip_address=psc_address.self_link,
        load_balancing_scheme="",
    )

    dns_zone = gcp.dns.ManagedZone(
        "bonsai-sensei-googleapis-zone",
        name="bonsai-sensei-googleapis",
        dns_name="googleapis.com.",
        visibility="private",
        private_visibility_config=gcp.dns.ManagedZonePrivateVisibilityConfigArgs(
            networks=[
                gcp.dns.ManagedZonePrivateVisibilityConfigNetworkArgs(
                    network_url=vpc.self_link,
                )
            ]
        ),
    )

    gcp.dns.RecordSet(
        "bonsai-sensei-googleapis-wildcard",
        name="*.googleapis.com.",
        type="A",
        ttl=300,
        managed_zone=dns_zone.name,
        rrdatas=[psc_address.address],
    )

    gcp.dns.RecordSet(
        "bonsai-sensei-googleapis-root",
        name="googleapis.com.",
        type="A",
        ttl=300,
        managed_zone=dns_zone.name,
        rrdatas=[psc_address.address],
    )
