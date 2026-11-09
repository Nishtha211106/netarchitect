import ipaddress, json
from pathlib import Path
from .errors import InvalidParameterError

PRESET_DIR = Path(__file__).resolve().parent.parent / "presets"
REQUIRED = ["name", "scope", "root_prefix", "sites", "links", "resiliency"]
SCOPES = {"campus", "metro", "wan"}

def load_preset(name: str) -> dict:
    path = PRESET_DIR / f"{name}.json"
    if not path.exists():
        raise InvalidParameterError(f"Unknown preset '{name}'. Choose: campus, metro, wan")
    with open(path) as f:
        return json.load(f)

def _num(v, label):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise InvalidParameterError(f"{label} must be a number, got {v!r}")
    if v <= 0:
        raise InvalidParameterError(f"{label} must be > 0, got {v}")

def validate_params(p: dict) -> dict:
    if not isinstance(p, dict):
        raise InvalidParameterError("Parameters must be a JSON object")
    for k in REQUIRED:
        if k not in p:
            raise InvalidParameterError(f"Missing required key: {k}")
    if p["scope"] not in SCOPES:
        raise InvalidParameterError(f"scope must be one of {sorted(SCOPES)}, got {p['scope']!r}")
    if not isinstance(p["root_prefix"], str):
        raise InvalidParameterError("root_prefix must be a string like '10.0.0.0/16'")
    try:
        net = ipaddress.ip_network(p["root_prefix"])
    except ValueError as e:
        raise InvalidParameterError(f"Bad root_prefix: {e}")
    if not isinstance(p["resiliency"], bool):
        raise InvalidParameterError("resiliency must be true/false")
    if not isinstance(p["sites"], list) or not p["sites"]:
        raise InvalidParameterError("sites must be a non-empty list")
    if not isinstance(p["links"], list) or not p["links"]:
        raise InvalidParameterError("links must be a non-empty list")

    total = 0
    for s in p["sites"]:
        if not isinstance(s, dict):
            raise InvalidParameterError("each site must be an object")
        _num(s.get("users"), f"users at {s.get('name')}")
        total += s["users"]
    for l in p["links"]:
        if not isinstance(l, dict):
            raise InvalidParameterError("each link must be an object")
        _num(l.get("distance_m"), f"distance of link {l.get('name')}")

    if total > net.num_addresses - 2:
        raise InvalidParameterError(
            f"{total} users cannot fit in {net} ({net.num_addresses - 2} usable addresses)")

    p = dict(p)  # don't mutate the caller's dict
    p.setdefault("multi_cloud", False)
    p.setdefault("routing_sites", len(p["sites"]))
    return p