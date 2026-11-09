from dataclasses import dataclass, field

@dataclass
class Decision:
    domain: str       # "media" | "routing" | "topology" | "subnetting"
    choice: str
    rationale: str

@dataclass
class Subnet:
    name: str
    hosts_requested: int
    prefix_len: int
    network: str
    mask: str
    wildcard: str
    first_usable: str
    last_usable: str
    broadcast: str
    gateway: str
    utilization: float      # percent

@dataclass
class Design:
    params: dict
    decisions: list = field(default_factory=list)   # list[Decision]
    requests: list = field(default_factory=list)    # [{"name":..., "hosts":...}]