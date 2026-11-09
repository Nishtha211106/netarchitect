import pytest
from netarchitect.routing import select_routing, select_topology


@pytest.mark.parametrize("n,expected", [
    (12, "OSPF Area 0"), (49, "OSPF Area 0"),
    (50, "Multi-Area OSPF"), (51, "Multi-Area OSPF"),
])
def test_subnet_boundary(n, expected):
    assert select_routing(n, 1, False).choice == expected


def test_multi_site_is_multi_area():
    assert select_routing(10, 3, False).choice == "Multi-Area OSPF"


def test_cloud_gets_bgp():
    assert "eBGP" in select_routing(10, 4, True).choice


def test_rationale_mentions_rfc():
    assert "RFC" in select_routing(10, 1, False).rationale


def test_resiliency_changes_output_and_rationale():
    for scope, sites in (("campus", 3), ("metro", 3), ("wan", 4)):
        on = select_topology(scope, True, sites)
        off = select_topology(scope, False, sites)
        assert on.choice != off.choice
        assert on.rationale != off.rationale