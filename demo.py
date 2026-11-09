from netarchitect.design import build_design
from netarchitect.params import load_preset

for name in ["campus", "metro", "wan"]:
    print(f"\n===== {name.upper()} =====")
    design = build_design(load_preset(name))
    for d in design.decisions:
        print(f"[{d.domain}] {d.choice}\n    {d.rationale}\n")
    print("Host requests for B:", design.requests)