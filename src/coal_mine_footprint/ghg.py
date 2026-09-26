"""Khí nhà kính và hệ số tiềm năng nóng lên toàn cầu (GWP)."""

from dataclasses import dataclass

# GWP 100 năm theo các báo cáo đánh giá của IPCC. AR6 dùng giá trị của CH4 có
# nguồn gốc hóa thạch. Báo cáo theo khung minh bạch của Thỏa thuận Paris dùng
# AR5, nên AR5 là mặc định.
GWP100: dict[str, dict[str, float]] = {
    "AR4": {"CO2": 1.0, "CH4": 25.0, "N2O": 298.0},
    "AR5": {"CO2": 1.0, "CH4": 28.0, "N2O": 265.0},
    "AR6": {"CO2": 1.0, "CH4": 29.8, "N2O": 273.0},
}
DEFAULT_GWP = "AR5"


def gwp_factors(gwp: str) -> dict[str, float]:
    """Trả về bộ hệ số GWP theo tên báo cáo IPCC (AR4, AR5, AR6)."""
    if gwp not in GWP100:
        raise ValueError(f"gwp phải là một trong {sorted(GWP100)}")
    return GWP100[gwp]


@dataclass(frozen=True)
class GasEmissions:
    """Khối lượng phát thải (tấn) theo từng loại khí."""

    co2_t: float = 0.0
    ch4_t: float = 0.0
    n2o_t: float = 0.0

    def __add__(self, other: "GasEmissions") -> "GasEmissions":
        return GasEmissions(
            self.co2_t + other.co2_t, self.ch4_t + other.ch4_t, self.n2o_t + other.n2o_t
        )

    def co2e_t(self, gwp: str = DEFAULT_GWP) -> float:
        """Phát thải quy đổi ra tấn CO2 tương đương."""
        f = gwp_factors(gwp)
        return self.co2_t * f["CO2"] + self.ch4_t * f["CH4"] + self.n2o_t * f["N2O"]
