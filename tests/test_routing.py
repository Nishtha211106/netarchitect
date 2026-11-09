import pytest
from netarchitect.routing import select_routing, select_topology


@pytest.mark.parametrize("n,expected", [
    (12, "OSPF Area 0"), (49, "OSPF Area 0"),
    (50, "Multi-Area OSPF"), (51, "Multi-Area OSPF"),
])
def test_subnet_boundary(n, expected):
    assert select_routing(n).choice == expected


def test_multi_site_is_multi_area():
    assert select_routing(10, num_sites=3).choice == "Multi-Area OSPF"


def test_cloud_gets_bgp():
    assert "eBGP" in select_routing(10, num_sites=4, has_cloud=True).choice


def test_negative_subnets_rejected():
    with pytest.raises(ValueError):
        select_routing(-1)


def test_resiliency_changes_output_and_rationale():
    for prof in ("campus", "metro", "wan"):
        on, off = select_topology(prof, True), select_topology(prof, False)
        assert on.choice != off.choice
        assert on.rationale != off.rationale