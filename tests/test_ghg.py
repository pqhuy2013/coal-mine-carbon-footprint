import pytest

from coal_mine_footprint.ghg import GasEmissions


def test_co2e_default_is_ar5():
    g = GasEmissions(co2_t=1, ch4_t=1, n2o_t=1)
    assert g.co2e_t() == pytest.approx(1 + 28 + 265)
    assert g.co2e_t("AR6") == pytest.approx(1 + 29.8 + 273)


def test_add():
    assert GasEmissions(1, 2, 3) + GasEmissions(1, 1, 1) == GasEmissions(2, 3, 4)


def test_unknown_gwp():
    with pytest.raises(ValueError):
        GasEmissions().co2e_t("AR3")
