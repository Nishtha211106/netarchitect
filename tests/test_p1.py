import pytest
from netarchitect.media import select_media
from netarchitect.routing import select_routing
from netarchitect.params import validate_params, load_preset
from netarchitect.design import build_design
from netarchitect.errors import *

@pytest.mark.parametrize("d,exp", [(100,"Cat6a"),(101,"OM4"),(400,"OM4"),
                                   (401,"OS2"),(5000,"LR"),(22000,"ER"),(50000,"amplified")])
def test_media_boundaries(d, exp):
    assert exp in select_media(d).choice

def test_copper_violation():
    with pytest.raises(PhysicalDistanceViolationError):
        select_media(101, requested="cat6a")

def test_copper_ok_at_100():
    assert "Cat6a" in select_media(100, requested="cat6a").choice

@pytest.mark.parametrize("bad", [0, -5, "abc", None, True])
def test_bad_distance(bad):
    with pytest.raises(InvalidParameterError):
        select_media(bad)

def test_rationale_has_real_numbers():
    assert "22 km" in select_media(22000).rationale

@pytest.mark.parametrize("n,exp", [(49,"Area 0"),(50,"Multi-Area")])
def test_routing_boundary(n, exp):
    assert exp in select_routing(n, 1, False).choice

def test_cloud_gives_bgp():
    assert "eBGP" in select_routing(10, 1, True).choice

def test_missing_key():
    with pytest.raises(InvalidParameterError):
        validate_params({"name": "x"})

@pytest.mark.parametrize("name", ["campus", "metro", "wan"])
def test_presets_build(name):
    assert len(build_design(load_preset(name)).decisions) >= 3