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
    )

    return vpc, subnet
