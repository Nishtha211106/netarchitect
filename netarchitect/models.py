from dataclasses import dataclass, field

@dataclass
class Decision:
    category: str      # "media", "transceiver", "routing", "topology", "subnetting"
    choice: str        # e.g. "OS2 SMF"
    rationale: str     # must contain the real numbers

@dataclass
class Subnet:
    name: str                  # department / VLAN name
    requested_hosts: int
    network: str               # dotted quad, e.g. "192.168.0.128"
    prefix: int
    mask: str
    wildcard: str
    first_usable: str
    last_usable: str
    broadcast: str
    gateway: str
    utilisation_pct: float
    vlan_id: int | None = None

@dataclass
class Design:
    profile: str
    decisions: list[Decision] = field(default_factory=list)
    subnets: list[Subnet] = field(default_factory=list)
    configs: dict[str, str] = field(default_factory=dict)  # device -> config text