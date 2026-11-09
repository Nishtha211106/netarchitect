"""Person 2: Cisco IOS config generators (switch + router/L3) with wildcard-safe ACLs."""
import ipaddress


def netmask(prefix: int) -> str:
    return str(ipaddress.IPv4Network(f"0.0.0.0/{prefix}").netmask)


def wildcard(prefix: int) -> str:
    """Inverse mask used by OSPF network statements and ACLs. /24 -> 0.0.0.255"""
    return str(ipaddress.IPv4Network(f"0.0.0.0/{prefix}").hostmask)


# Fake list until Person 3's vlsm.py is ready
FAKE_SUBNETS = [
    {"name": "STAFF", "vlan": 10, "network": "10.0.0.0",   "prefix": 24, "gateway": "10.0.0.1"},
    {"name": "LAB",   "vlan": 20, "network": "10.0.1.0",   "prefix": 25, "gateway": "10.0.1.1"},
    {"name": "GUEST", "vlan": 30, "network": "10.0.1.128", "prefix": 26, "gateway": "10.0.1.129"},
]


def gen_switch_config(hostname, subnets, resiliency=False):
    vlans = ",".join(str(s["vlan"]) for s in subnets)
    out = [f"hostname {hostname}", "!", "spanning-tree mode rapid-pvst", "!"]
    for s in subnets:
        out += [f"vlan {s['vlan']}", f" name {s['name']}"]
    out.append("!")
    uplinks = ["GigabitEthernet0/1"]
    if resiliency:
        uplinks.append("GigabitEthernet0/2")  # redundant uplink, RSTP blocks the loop
    for port in uplinks:
        out += [f"interface {port}",
                " description UPLINK",
                " switchport mode trunk",
                f" switchport trunk allowed vlan {vlans}",
                " no shutdown", "!"]
    return "\n".join(out) + "\n"


def gen_acl(subnets, guest_name="GUEST"):
    """Block GUEST from reaching every other internal subnet, allow the rest."""
    guest = next((s for s in subnets if s["name"] == guest_name), None)
    if guest is None:
        return ""
    lines = [f"ip access-list extended BLOCK-{guest_name}"]
    for s in subnets:
        if s is guest:
            continue
        lines.append(f" deny ip {guest['network']} {wildcard(guest['prefix'])} "
                     f"{s['network']} {wildcard(s['prefix'])}")
    lines.append(" permit ip any any")
    lines.append("!")
    return "\n".join(lines) + "\n"


def gen_router_config(hostname, subnets, router_id, area_default="0"):
    out = [f"hostname {hostname}", "!", "ip routing", "!"]
    acl = gen_acl(subnets)
    guest_acl = "BLOCK-GUEST" if acl else None
    for s in subnets:
        out += [f"interface Vlan{s['vlan']}",
                f" description {s['name']} gateway",
                f" ip address {s['gateway']} {netmask(s['prefix'])}"]
        if guest_acl and s["name"] == "GUEST":
            out.append(f" ip access-group {guest_acl} in")
        out += [" no shutdown", "!"]
    if acl:
        out.append(acl.rstrip("\n"))
    out += ["router ospf 1", f" router-id {router_id}"]
    for s in subnets:
        area = s.get("area", area_default)
        out.append(f" network {s['network']} {wildcard(s['prefix'])} area {area}")
        out.append(f" passive-interface Vlan{s['vlan']}")
    out.append("!")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    print(gen_switch_config("SW-CAMPUS", FAKE_SUBNETS, resiliency=True))
    print(gen_router_config("CORE-1", FAKE_SUBNETS, "1.1.1.1"))