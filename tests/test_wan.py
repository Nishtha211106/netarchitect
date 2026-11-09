from netarchitect.wan_extras import (covering_supernet, gen_area_range,
                                     gen_bgp_config, gen_ipsec_skeleton)


def test_supernet_four_24s():
    nets = ["10.1.0.0/24", "10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
    assert str(covering_supernet(nets)) == "10.1.0.0/22"


def test_supernet_non_adjacent_still_covers():
    assert str(covering_supernet(["10.1.0.0/24", "10.1.3.0/24"])) == "10.1.0.0/22"


def test_area_range_uses_subnet_mask():
    line, why = gen_area_range(1, ["10.1.0.0/24", "10.1.1.0/24"])
    assert line == " area 1 range 10.1.0.0 255.255.254.0"
    assert "10.1.0.0/23" in why


def test_bgp_neighbor_and_network_mask():
    cfg = gen_bgp_config(65001, "1.1.1.1",
                         [{"ip": "203.0.113.2", "remote_as": 65002}],
                         ["10.0.0.0/16"])
    assert "neighbor 203.0.113.2 remote-as 65002" in cfg
    assert "network 10.0.0.0 mask 255.255.0.0" in cfg


def test_ipsec_acl_is_wildcard():
    cfg = gen_ipsec_skeleton("198.51.100.2", "10.0.0.0/24", "10.2.0.0/24")
    assert "permit ip 10.0.0.0 0.0.0.255 10.2.0.0 0.0.0.255" in cfg
    assert "crypto map WAN-MAP" in cfg