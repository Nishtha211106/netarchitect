from netarchitect.configs import (wildcard, netmask, gen_switch_config,
                                  gen_router_config, gen_acl, FAKE_SUBNETS)


def test_wildcards():
    assert wildcard(24) == "0.0.0.255"
    assert wildcard(30) == "0.0.0.3"
    assert wildcard(23) == "0.0.1.255"
    assert wildcard(26) == "0.0.0.63"


def test_netmask():
    assert netmask(25) == "255.255.255.128"


def test_switch_has_allowed_vlan_and_rstp():
    cfg = gen_switch_config("SW1", FAKE_SUBNETS)
    assert "switchport trunk allowed vlan 10,20,30" in cfg
    assert "spanning-tree mode rapid-pvst" in cfg


def test_resiliency_adds_second_uplink():
    assert "GigabitEthernet0/2" not in gen_switch_config("SW1", FAKE_SUBNETS, False)
    assert "GigabitEthernet0/2" in gen_switch_config("SW1", FAKE_SUBNETS, True)


def test_no_subnet_mask_in_ospf_or_acl():
    cfg = gen_router_config("R1", FAKE_SUBNETS, "1.1.1.1")
    for line in cfg.splitlines():
        s = line.strip()
        if s.startswith(("network", "deny", "permit")):
            assert "255.255.255" not in s, line


def test_acl_uses_wildcards():
    acl = gen_acl(FAKE_SUBNETS)
    assert "deny ip 10.0.1.128 0.0.0.63 10.0.0.0 0.0.0.255" in acl