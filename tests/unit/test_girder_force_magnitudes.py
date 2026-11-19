import pytest
import xarray as xr

from osdagbridge.core.bridge_types.plate_girder.designer import _absolute_force_maximum


@pytest.mark.parametrize("values", [[[-300, 120], [20, -30]], [[-300, -120], [-20, -30]]])
def test_force_reduction_keeps_the_largest_negative_magnitude(values):
    forces = xr.DataArray(values, dims=("Element", "Component"),
                          coords={"Component": ["Mz_i", "Mz_j"]})
    assert _absolute_force_maximum(forces, "Mz_i", "Mz_j") == 300
