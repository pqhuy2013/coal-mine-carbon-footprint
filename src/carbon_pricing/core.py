"""Các phép tính định giá carbon cốt lõi."""


def carbon_cost(emissions_tco2e: float, price_per_tonne: float) -> float:
    """Trả về chi phí của lượng phát thải (tCO2e) theo giá carbon mỗi tấn."""
    if emissions_tco2e < 0:
        raise ValueError("emissions_tco2e phải không âm")
    if price_per_tonne < 0:
        raise ValueError("price_per_tonne phải không âm")
    return emissions_tco2e * price_per_tonne


def price_path(start_price: float, growth_rate: float, years: int) -> list[float]:
    """Trả về lộ trình giá carbon tăng theo một tỷ lệ cố định mỗi năm.

    Phần tử đầu tiên là ``start_price``; mỗi năm tiếp theo được nhân với
    ``1 + growth_rate``. ``years`` là số mức giá được trả về.
    """
    if start_price < 0:
        raise ValueError("start_price phải không âm")
    if growth_rate <= -1:
        raise ValueError("growth_rate phải lớn hơn -1")
    if years < 0:
        raise ValueError("years phải không âm")
    return [start_price * (1 + growth_rate) ** t for t in range(years)]
