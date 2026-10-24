"""Deterministic texture synthesis tests; require no Blender/GPU."""
import ast
from pathlib import Path
import numpy as np
import pytest
from goshman.pbr_maps import PROFILES,make_maps

@pytest.mark.parametrize("material", list(PROFILES))
def test_map_channels_are_valid_and_reproducible(material):
    maps=make_maps(material,"#808080",64)
    assert set(maps)=={"base_color","roughness","metallic","normal"}
    for pixels in maps.values():
        assert pixels.shape==(64,64,4)
        assert pixels.dtype==np.float32
        assert np.isfinite(pixels).all()
        assert pixels.min()>=0 and pixels.max()<=1
    assert maps["normal"][:,:,2].mean()>.83
    assert maps["base_color"][:,:,:3].std()>.002
    assert np.array_equal(maps["base_color"],make_maps(material,"#808080",64)["base_color"])

def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        make_maps("Unknown","#808080",128)
    with pytest.raises(ValueError):
        make_maps("Scales","#808080",63)

def test_blender_integration_source_parseable():
    path=Path(__file__).parents[1]/"goshman"/"pbr_blender.py"
    module=ast.parse(path.read_text(encoding="utf-8"))
    functions={node.name for node in ast.walk(module) if isinstance(node,ast.FunctionDef)}
    assert {"ensure_uv","attach_maps"}.issubset(functions)
