import ipaddress
import random

import pytest

from netarchitect.errors import AddressSpaceExhaustedError, InvalidParameterError
from netarchitect.vlsm import (allocate, block_for_hosts, describe_block, int_to_ip,
                               ip_to_int, parse_cidr, wildcard_mask)


@pytest.mark.parametrize("prefix,expected", [
    (0, "255.255.255.255"), (24, "0.0.0.255"), (26, "0.0.0.63"),
    (30, "0.0.0.3"), (31, "0.0.0.1"), (32, "0.0.0.0"),
])
def test_wildcard_mask(prefix, expected):
    assert wildcard_mask(prefix) == expected


def test_wildcard_matches_ipaddress_for_every_prefix():
    for p in range(33):
        assert wildcard_mask(p) == str(ipaddress.ip_network(f"0.0.0.0/{p}").hostmask)


def test_ip_round_trip():
    assert ip_to_int("0.0.0.1") == 1
    assert ip_to_int("255.255.255.255") == 2**32 - 1
    assert int_to_ip(ip_to_int("192.168.0.128")) == "192.168.0.128"


@pytest.mark.parametrize("hosts,prefix", [(100, 25), (50, 26), (20, 27), (126, 25),
                                          (127, 24), (2, 30), (1, 30)])
def test_block_prefix(hosts, prefix):
    assert block_for_hosts(hosts)[1] == prefix


def test_worked_example():
    subnets, _ = allocate("192.168.0.0/24", [("A", 20), ("B", 100), ("C", 50)])
    got = [(s.network, s.prefix, s.first_usable, s.last_usable, s.broadcast) for s in subnets]
    assert got == [
        ("192.168.0.0", 25, "192.168.0.1", "192.168.0.126", "192.168.0.127"),
        ("192.168.0.128", 26, "192.168.0.129", "192.168.0.190", "192.168.0.191"),
        ("192.168.0.192", 27, "192.168.0.193", "192.168.0.222", "192.168.0.223"),
    ]
    assert subnets[0].gateway == "192.168.0.1"


def test_exact_fit_passes_and_one_more_host_fails():
    allocate("192.168.0.0/24", [("a", 126), ("b", 126)])          # 128 + 128 = 256
    with pytest.raises(AddressSpaceExhaustedError):
        allocate("192.168.0.0/24", [("a", 126), ("b", 127)])      # second needs 256
    allocate("192.168.0.0/24", [("a", 254)])
    with pytest.raises(AddressSpaceExhaustedError):
        allocate("192.168.0.0/24", [("a", 255)])


def _ranges(subnets):
    return [(ip_to_int(s.network), ip_to_int(s.network) + (1 << (32 - s.prefix))) for s in subnets]


def _assert_no_overlap(subnets):
    r = _ranges(subnets)
    for i in range(len(r)):
        for j in range(i + 1, len(r)):
            assert r[i][1] <= r[j][0] or r[j][1] <= r[i][0]


def test_no_overlap_and_alignment_random():
    rng = random.Random(42)
    for _ in range(200):
        reqs = [(f"n{i}", rng.randint(1, 300)) for i in range(rng.randint(1, 8))]
        subnets, _ = allocate("10.0.0.0/16", reqs)
        _assert_no_overlap(subnets)
        for s in subnets:
            assert ip_to_int(s.network) % (1 << (32 - s.prefix)) == 0


def test_cross_check_with_ipaddress():
    subnets, _ = allocate("10.0.0.0/16", [("a", 1000), ("b", 500), ("c", 60), ("d", 2), ("e", 1)])
    for s in subnets:
        ref = ipaddress.ip_network(f"{s.network}/{s.prefix}")
        assert s.mask == str(ref.netmask)
        assert s.wildcard == str(ref.hostmask)
        assert s.broadcast == str(ref.broadcast_address)
        assert s.first_usable == str(ref.network_address + 1)
        assert s.last_usable == str(ref.broadcast_address - 1)


def test_slash31_and_slash32():
    p2p = describe_block("link", 2, ip_to_int("10.0.0.0"), 31)
    assert (p2p.first_usable, p2p.last_usable) == ("10.0.0.0", "10.0.0.1")
    lo = describe_block("lo0", 1, ip_to_int("10.0.0.9"), 32)
    assert lo.first_usable == lo.last_usable == "10.0.0.9"


@pytest.mark.parametrize("bad", [0, -5, "abc", None])
def test_bad_host_requests(bad):
    with pytest.raises(InvalidParameterError):
        block_for_hosts(bad)


def test_bad_root():
    with pytest.raises(InvalidParameterError):
        parse_cidr("192.168.0.5/24")    # host bits set
    with pytest.raises(InvalidParameterError):
        parse_cidr("192.168.0.0/33")