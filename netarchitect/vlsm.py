from .errors import AddressSpaceExhaustedError, InvalidParameterError
from .models import Decision, Subnet

FULL = 0xFFFFFFFF  # 32 one-bits


# ---------- helpers: dotted-quad <-> 32-bit int ----------
def ip_to_int(ip: str) -> int:
    parts = ip.strip().split(".")
    if len(parts) != 4:
        raise InvalidParameterError(f"'{ip}' is not a dotted-quad IPv4 address")
    value = 0
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            raise InvalidParameterError(f"Bad octet '{part}' in '{ip}'")
        value = (value << 8) | int(part)
    return value


def int_to_ip(n: int) -> str:
    return ".".join(str((n >> shift) & 0xFF) for shift in (24, 16, 8, 0))


# ---------- masks ----------
def _check_prefix(prefix: int) -> None:
    if not isinstance(prefix, int) or isinstance(prefix, bool) or not 0 <= prefix <= 32:
        raise InvalidParameterError(f"Prefix must be an integer 0-32, got {prefix!r}")


def prefix_to_mask_int(prefix: int) -> int:
    _check_prefix(prefix)
    return (FULL << (32 - prefix)) & FULL   # & FULL stops Python's unbounded ints


def wildcard_mask(prefix: int) -> str:
    # ~ on a Python int goes negative, so mask back to 32 bits
    return int_to_ip(~prefix_to_mask_int(prefix) & FULL)


def parse_cidr(cidr: str) -> tuple[int, int]:
    try:
        ip_text, prefix_text = cidr.split("/")
        prefix = int(prefix_text)
    except ValueError:
        raise InvalidParameterError(f"'{cidr}' is not in a.b.c.d/n form") from None
    _check_prefix(prefix)
    network = ip_to_int(ip_text)
    host_bits = ~prefix_to_mask_int(prefix) & FULL
    if network & host_bits:
        raise InvalidParameterError(
            f"{cidr} has host bits set; the network address would be "
            f"{int_to_ip(network & ~host_bits & FULL)}/{prefix}"
        )
    return network, prefix


# ---------- block sizing ----------
def block_for_hosts(hosts: int) -> tuple[int, int]:
    """Return (block_size, prefix) for a host request. Needs hosts + 2 addresses."""
    if not isinstance(hosts, int) or isinstance(hosts, bool) or hosts < 1:
        raise InvalidParameterError(f"Host request must be an integer >= 1, got {hosts!r}")
    needed = hosts + 2                          # + network + broadcast
    size = 1 << (needed - 1).bit_length()       # next power of two >= needed
    prefix = 32 - (size.bit_length() - 1)
    return size, prefix


def describe_block(name: str, hosts: int, network: int, prefix: int,
                   vlan_id: int | None = None) -> Subnet:
    mask = prefix_to_mask_int(prefix)
    wild = ~mask & FULL
    broadcast = network | wild
    if prefix == 32:                 # loopback: one address
        first = last = network
    elif prefix == 31:               # RFC 3021 point-to-point: both addresses usable
        first, last = network, broadcast
    else:
        first, last = network + 1, broadcast - 1
    usable = last - first + 1
    return Subnet(
        name=name,
        requested_hosts=hosts,
        network=int_to_ip(network),
        prefix=prefix,
        mask=int_to_ip(mask),
        wildcard=int_to_ip(wild),
        first_usable=int_to_ip(first),
        last_usable=int_to_ip(last),
        broadcast=int_to_ip(broadcast),
        gateway=int_to_ip(first),
        utilisation_pct=round(100 * hosts / usable, 1),
        vlan_id=vlan_id,
    )


# ---------- the allocator ----------
def allocate(root: str, requests: list[tuple[str, int]]) -> tuple[list[Subnet], Decision]:
    if not requests:
        raise InvalidParameterError("No host requests supplied")
    root_net, root_prefix = parse_cidr(root)
    root_size = 1 << (32 - root_prefix)
    root_end = root_net + root_size              # exclusive

    ordered = sorted(requests, key=lambda r: r[1], reverse=True)  # largest first
    cursor = root_net
    subnets: list[Subnet] = []
    for name, hosts in ordered:
        size, prefix = block_for_hosts(hosts)
        if cursor + size > root_end:
            raise AddressSpaceExhaustedError(
                f"Cannot fit '{name}' ({hosts} hosts needs a /{prefix} = {size} addresses): "
                f"only {root_end - cursor} addresses left in {root}"
            )
        assert cursor % size == 0, "alignment broken"   # holds because sizes descend
        subnets.append(describe_block(name, hosts, cursor, prefix))
        cursor += size

    used = cursor - root_net
    requested = sum(s.requested_hosts for s in subnets)
    usable_total = sum((1 << (32 - s.prefix)) - 2 for s in subnets)
    rationale = (
        f"Allocated {len(subnets)} subnets from {root} ({root_size} addresses) using VLSM "
        f"(RFC 1878, RFC 4632). Requests were sorted largest-first so every power-of-two "
        f"block starts on a multiple of its own size with no gaps or overlaps. Each block "
        f"is the smallest power of two holding hosts + 2 (network and broadcast address). "
        f"{used} of {root_size} addresses are allocated ({used / root_size:.1%} of the root); "
        f"{requested} requested hosts fit in {usable_total} usable addresses "
        f"({requested / usable_total:.1%} efficiency)."
    )
    return subnets, Decision("subnetting", f"VLSM allocation inside {root}", rationale)