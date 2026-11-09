"""Person 2: WAN extras - route summarisation, BGP, IPsec skeleton."""
import ipaddress


def covering_supernet(networks):
    """Smallest single block that covers every network in the list."""
    nets = [ipaddress.IPv4Network(n) for n in networks]
    lo = min(int(n.network_address) for n in nets)
    hi = max(int(n.broadcast_address) for n in nets)
    for prefix in range(32, -1, -1):
        cand = ipaddress.IPv4Network((lo, prefix), strict=False)
        if int(cand.broadcast_address) >= hi:
            return cand


def gen_area_range(area, networks):
    """ABR summary. NOTE: 'area range' takes a SUBNET mask, not a wildcard."""
    sup = covering_supernet(networks)
    line = f" area {area} range {sup.network_address} {sup.netmask}"
    why = (f"Summarised {len(networks)} routes of area {area} into {sup} at the ABR "
           f"to shrink the routing table and hide flaps from other areas.")
    return line, why


def gen_bgp_config(local_as, router_id, neighbors, networks):
    """neighbors: [{'ip': '203.0.113.2', 'remote_as': 65002, 'desc': 'CLOUD'}]
    BGP 'network' uses a SUBNET mask (not wildcard)."""
    out = [f"router bgp {local_as}",
           f" bgp router-id {router_id}",
           " bgp log-neighbor-changes"]
    for n in neighbors:
        out.append(f" neighbor {n['ip']} remote-as {n['remote_as']}")
        out.append(f" neighbor {n['ip']} description {n.get('desc', 'PEER')}")
    for net in networks:
        i = ipaddress.IPv4Network(net)
        out.append(f" network {i.network_address} mask {i.netmask}")
    out.append("!")
    return "\n".join(out) + "\n"


def gen_ipsec_skeleton(peer_ip, local_net, remote_net,
                       wan_interface="GigabitEthernet0/0"):
    """Site-to-site IPsec. The VPN ACL uses WILDCARD masks."""
    l = ipaddress.IPv4Network(local_net)
    r = ipaddress.IPv4Network(remote_net)
    return "\n".join([
        "crypto isakmp policy 10",
        " encryption aes 256",
        " hash sha256",
        " authentication pre-share",
        " group 14",
        " lifetime 86400",
        "!",
        f"crypto isakmp key CHANGE_ME_PSK address {peer_ip}",
        "!",
        "crypto ipsec transform-set TS-AES esp-aes 256 esp-sha256-hmac",
        " mode tunnel",
        "!",
        "ip access-list extended VPN-TRAFFIC",
        f" permit ip {l.network_address} {l.hostmask} {r.network_address} {r.hostmask}",
        "!",
        "crypto map WAN-MAP 10 ipsec-isakmp",
        f" set peer {peer_ip}",
        " set transform-set TS-AES",
        " match address VPN-TRAFFIC",
        "!",
        f"interface {wan_interface}",
        " crypto map WAN-MAP",
        "!",
    ]) + "\n"