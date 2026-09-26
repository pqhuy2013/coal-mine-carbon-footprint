from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parents[1] / "app.py")


def test_app_computes_inventory():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception

    at.number_input(key="production").set_value(1_000_000)
    at.number_input(key="electricity_kwh").set_value(10_000_000)
    at.run()
    assert not at.exception
    assert not at.error

    metrics = {m.label: m.value for m in at.metric}
    # CH4: 20.500.000 m³ x 0,67 kg/m³ x 28 = 384.580 tCO2e;
    # điện: 10.000 MWh x 0,6592 = 6.592 tCO2e.
    assert metrics["Scope 2 (tCO2e)"] == "6.592,0"
    assert metrics["Tổng phát thải (tCO2e)"] == "391.172,0"
    assert metrics["Cường độ (kgCO2e/tấn than)"] == "391,2"


def test_app_shows_error_for_invalid_input():
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.number_input(key="production").set_value(1000)
    at.number_input(key="recovered_m3").set_value(1e9)
    at.run()
    assert not at.exception
    assert at.error
