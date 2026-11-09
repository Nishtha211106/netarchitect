import argparse
import json
import sys
from pathlib import Path

from .errors import NetArchitectError
from .models import Design
from .vlsm import allocate

PRESET_DIR = Path(__file__).resolve().parent.parent / "presets"


def load_params(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        sys.exit(f"Error: file not found: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"Error: {path} is not valid JSON (line {e.lineno}, column {e.colno}): {e.msg}")


def build(params: dict) -> Design:
    try:
        from .design import build_design      # P1's integration function
    except ImportError:
        build_design = None
    if build_design:
        return build_design(params)
    # standalone fallback so you can test before P1 lands
    subnets, decision = allocate(params["root"], [tuple(r) for r in params["requests"]])
    return Design(profile=params.get("name", "custom"), decisions=[decision], subnets=subnets)


def print_design(design: Design) -> None:
    print(f"\n=== {design.profile} ===")
    for d in design.decisions:
        print(f"[{d.category}] {d.choice}\n    {d.rationale}")
    if design.subnets:
        print(f"\n{'Name':<12}{'Network':<18}{'Mask':<17}{'Wildcard':<14}{'Gateway':<16}{'Broadcast':<16}{'Util%':>6}")
        for s in design.subnets:
            print(f"{s.name:<12}{s.network + '/' + str(s.prefix):<18}{s.mask:<17}"
                  f"{s.wildcard:<14}{s.gateway:<16}{s.broadcast:<16}{s.utilisation_pct:>6}")


def export(design: Design, export_dir: Path) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    if not design.configs:
        print("\n(no device configs in this design yet, nothing exported)")
        return
    out = export_dir / f"{design.profile}.cfg"
    with open(out, "w", encoding="utf-8") as f:
        for device, text in design.configs.items():
            f.write(f"! ===== {device} =====\n{text}\n\n")
    print(f"\nExported {out}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="netarchitect", description="NetArchitect planning engine")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--preset", choices=["campus", "metro", "wan"])
    src.add_argument("--custom", type=Path, metavar="FILE.json")
    parser.add_argument("--export-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    path = PRESET_DIR / f"{args.preset}.json" if args.preset else args.custom
    params = load_params(path)
    try:
        design = build(params)
    except NetArchitectError as e:
        sys.exit(f"Error: {e}")
    except KeyError as e:
        sys.exit(f"Error: missing key {e} in {path}")
    print_design(design)
    if args.export_dir:
        export(design, args.export_dir)


if __name__ == "__main__":
    main()