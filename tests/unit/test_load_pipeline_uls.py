import numpy as np
import pytest
import xarray as xr

from osdagbridge.core.bridge_types.plate_girder.designer import _require_uls_forces


def test_uls_requires_solved_finite_forces_but_accepts_zero():
    coords = {"Loadcase": ["Envelope ULS"], "Element": [1],
              "Component": ["Mz_i", "Mz_j", "Vy_i", "Vy_j"]}
    dataset = xr.Dataset({"forces": (("Loadcase", "Element", "Component"),
                                     np.zeros((1, 1, 4)))}, coords=coords)
    _require_uls_forces(dataset, "Envelope ULS", "G1", [1])
    with pytest.raises(ValueError, match="Enable ULS"):
        _require_uls_forces(dataset, None, "G1", [1])
    with pytest.raises(ValueError, match="G1"):
        _require_uls_forces(dataset.drop_sel(Component="Vy_j"), "Envelope ULS", "G1", [1])
    dataset.forces.loc[{"Component": "Vy_j"}] = np.nan
    with pytest.raises(ValueError, match="G1"):
        _require_uls_forces(dataset, "Envelope ULS", "G1", [1])
