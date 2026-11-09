from .errors import PhysicalDistanceViolationError, InvalidParameterError
from .models import Decision

COPPER = {"cat6a", "copper", "utp", "cat6", "cat5e"}

def _fmt(d):
    return f"{d / 1000:g} km" if d >= 1000 else f"{d:g} m"

def select_media(distance_m, requested=None):
    if isinstance(distance_m, bool) or not isinstance(distance_m, (int, float)) or distance_m <= 0:
        raise InvalidParameterError(f"distance must be a positive number, got {distance_m!r}")
    d = _fmt(distance_m)

    if requested and str(requested).lower() in COPPER and distance_m > 100:
        raise PhysicalDistanceViolationError(
            f"Copper requested for {d}, but 10GBASE-T (IEEE 802.3an) is limited to 100 m; "
            f"signal attenuation and crosstalk make the link unreliable beyond that.")

    if distance_m <= 100:
        return Decision("media", "Cat6a (10GBASE-T)",
            f"Selected Cat6a because link distance ({d}) is within the 100 m limit "
            f"of 10GBASE-T (IEEE 802.3an).")

    if distance_m <= 400:
        return Decision("media", "OM4 MMF (10GBASE-SR)",
            f"Selected OM4 multimode fibre because link distance ({d}) exceeds the 100 m "
            f"copper limit but is within the 400 m reach of 10GBASE-SR at 850 nm, "
            f"where modal dispersion limits multimode fibre.")

    if distance_m <= 10_000:
        tx, why = "10GBASE-LR", "within the ~10 km reach of LR (1310 nm)"
    elif distance_m <= 40_000:
        tx, why = "10GBASE-ER", ("beyond the ~10 km LR reach but within the ~40 km ER reach "
                                 "(1550 nm, larger optical power budget)")
    else:
        return Decision("media", "OS2 SMF (amplified / ZR-DWDM)",
            f"WARNING: link distance ({d}) exceeds the ~40 km reach of 10GBASE-ER. "
            f"Selected OS2 single-mode fibre, but an optical amplifier, regenerator or "
            f"ZR/DWDM optics (or a leased carrier circuit) is required.")

    return Decision("media", f"OS2 SMF ({tx})",
        f"Selected OS2 single-mode fibre because link distance ({d}) exceeds the 400 m "
        f"limit of OM4 multimode fibre; {tx} chosen because {d} is {why}.")