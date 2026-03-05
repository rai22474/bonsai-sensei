import pulumi_gcp as gcp


def create_network(region: str) -> tuple[gcp.compute.Network, gcp.compute.Subnetwork]:
    vpc = gcp.compute.Network(
        "bonsai-sensei-vpc",
        name="bonsai-sensei-vpc",
        auto_create_subnetworks=False,
    )

    subnet = gcp.compute.Subnetwork(
        "bonsai-sensei-subnet",
        name="bonsai-sensei-subnet",
        region=region,
        network=vpc.id,
        ip_cidr_range="10.8.0.0/24",
    )

    router = gcp.compute.Router(
        "bonsai-sensei-router",
        name="bonsai-sensei-router",
        region=region,
        network=vpc.id,
    )

    gcp.compute.RouterNat(
        "bonsai-sensei-nat",
        name="bonsai-sensei-nat",
        router=router.name,
        region=region,
        nat_ip_allocate_option="AUTO_ONLY",
        source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES",
    )

    return vpc, subnet
