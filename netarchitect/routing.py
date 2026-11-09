from .models import Decision

def select_routing(num_subnets, num_sites, multi_cloud):
    n, s = num_subnets, num_sites
    if multi_cloud:
        return Decision("routing", "eBGP + Multi-Area OSPF",
            f"Selected eBGP (RFC 4271) between routing domains, with multi-area OSPF "
            f"inside each, because the design crosses a multi-cloud boundary ({s} sites, "
            f"{n} subnets); BGP gives policy control and routing-domain isolation "
            f"that an IGP cannot.")
    if s > 1 or n >= 50:
        reason = (f"{s} sites" if s > 1 else f"{n} subnets (>= 50)")
        return Decision("routing", "Multi-Area OSPF",
            f"Selected multi-area OSPF because the design has {reason} ({n} subnets total); "
            f"areas contain LSA flooding and SPF recalculation (RFC 2328) and allow "
            f"route summarisation at ABRs.")
    return Decision("routing", "OSPF Area 0",
        f"Selected single-area OSPF (Area 0) because the design has {n} subnets (< 50) "
        f"in {s} site within one autonomous system; link-state routing (RFC 2328) "
        f"converges quickly with a single flooding domain.")

def select_topology(scope, resiliency, num_sites):
    if scope == "campus":
        if resiliency:
            return Decision("topology", "Three-tier (access/distribution/core) with redundant uplinks",
                f"Selected a three-tier campus design across {num_sites} buildings; "
                f"resiliency is required, so each access switch is dual-homed to two "
                f"distribution switches and RSTP (802.1w) blocks loops.")
        return Decision("topology", "Three-tier (access/distribution/core)",
            f"Selected a three-tier design across {num_sites} buildings with single uplinks "
            f"because resiliency was not requested.")
    if scope == "metro":
        if resiliency:
            return Decision("topology", "Dual-homed MAN",
                f"Selected a dual-homed topology because resiliency is required: each of the "
                f"{num_sites - 1} remote sites has two diverse paths, so one fibre cut "
                f"does not isolate a site.")
        return Decision("topology", "Hub-and-spoke MAN",
            f"Selected hub-and-spoke with the HQ as hub for {num_sites - 1} remote sites, "
            f"because resiliency was not requested.")
    if resiliency:
        return Decision("topology", "Partial-mesh WAN",
            f"Selected a partial mesh across {num_sites} sites because resiliency is "
            f"required; multiple paths survive a single circuit failure.")
    return Decision("topology", "Hub-and-spoke WAN",
        f"Selected hub-and-spoke across {num_sites} sites because resiliency was not requested.")