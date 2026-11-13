"""IRC 6:2017 Cl. 211.2 braking force — hand-calculated checks.

Hand calculations (IRC 6:2017 Cl. 204.1 vehicle data):
  Class A train  = 2.7+2.7+11.4+11.4+6.8x4 t      = 55.4 t  = 543 474 N
  Class 70R (W)  = 8+12+12+17+17+17+17 t          = 100 t   = 981 000 N
  1-2 lanes : 20% of Class A                      = 11.08 t = 108 694.8 N
  3+ lanes  : 11.08 t + 5% of 70R (5 t)           = 16.08 t = 157 744.8 N
"""
import pytest

from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

G = 9.81  # N per kg (as used for the stored wheel loads)


def test_vehicle_totals_match_irc6_tonnage():
    assert sum(IRC6_2017.cl_204_1_ClassA_vehicle()["wheel_loads"]) == pytest.approx(55.4e3 * G)
    assert sum(IRC6_2017.cl_204_1_Class70R_vehicle_wheel()["wheel_loads"]) == pytest.approx(100e3 * G)


@pytest.mark.parametrize("lanes", [1, 2])
def test_one_or_two_lanes_is_20_percent_of_class_a(lanes):
    assert IRC6_2017.cl_211_2_braking_force(lanes) == pytest.approx(0.20 * 55.4e3 * G)


def test_three_lanes_adds_5_percent_of_70r():
    assert IRC6_2017.cl_211_2_braking_force(3) == pytest.approx(0.20 * 55.4e3 * G + 0.05 * 100e3 * G)


@pytest.mark.parametrize("lanes", [0, -1, None])
def test_missing_or_invalid_lanes_raise_instead_of_returning_zero(lanes):
    with pytest.raises(ValueError):
        IRC6_2017.cl_211_2_braking_force(lanes)
