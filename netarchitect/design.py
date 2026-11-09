from .params import validate_params
from .media import select_media
from .routing import select_routing, select_topology
from .models import Design

def build_design(params: dict) -> Design:
    p = validate_params(params)
    d = Design(params=p)

    for l in p["links"]:
        dec = select_media(l["distance_m"], l.get("requested_media"))
        dec.rationale = f"[{l['name']}] " + dec.rationale
        d.decisions.append(dec)

    # host requests for B's VLSM: one per site, one /30-sized per point-to-point link
    d.requests = [{"name": s["name"], "hosts": s["users"]} for s in p["sites"]]
    d.requests += [{"name": f"P2P-{l['name']}", "hosts": 2}
                   for l in p["links"] if l.get("p2p", True)]

    d.decisions.append(select_routing(len(d.requests), p["routing_sites"], p["multi_cloud"]))
    d.decisions.append(select_topology(p["scope"], p["resiliency"], len(p["sites"])))
    return d