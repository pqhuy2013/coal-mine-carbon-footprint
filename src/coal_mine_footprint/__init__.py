"""Ứng dụng tính toán dấu chân carbon cho mỏ than."""

from coal_mine_footprint.methane import (
    EmissionFactorLevel,
    MethaneEmissions,
    MiningMethod,
    fugitive_methane,
)

__all__ = ["EmissionFactorLevel", "MethaneEmissions", "MiningMethod", "fugitive_methane"]
__version__ = "0.1.0"
