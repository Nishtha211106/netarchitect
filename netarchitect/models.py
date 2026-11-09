from dataclasses import dataclass, field

@dataclass
class Decision:
    domain: str        # "media" | "routing" | "topology" | "subnetting"
    choice: str
    rationale: str     # must contain the real numbers

@dataclass
class Subnet:
    name: str
    requested_hosts: int
    network: str
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
    params: dict = field(default_factory=dict)
    profile: str = ""
    decisions: list = field(default_factory=list)   # list[Decision]
    requests: list = field(default_factory=list)    # [{"name":..., "hosts":...}]
    subnets: list = field(default_factory=list)     # list[Subnet]
    configs: dict = field(default_factory=dict)     # device -> config text