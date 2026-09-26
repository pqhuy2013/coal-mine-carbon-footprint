"""Giao diện web kiểm kê khí nhà kính cho mỏ than hầm lò.

Chạy ứng dụng: ``streamlit run app.py``
"""

from datetime import date

import pandas as pd
import streamlit as st

from coal_mine_footprint.combustion import FUELS, CombustionType
from coal_mine_footprint.inventory import (
    DEFAULT_EXPLOSIVE_EF,
    FuelUse,
    InventoryInput,
    MethaneTier,
    compute_inventory,
)
from coal_mine_footprint.methane import (
    TIER1_MINING_EF,
    TIER1_POST_MINING_EF,
    EmissionFactorLevel,
    MiningMethod,
)
from coal_mine_footprint.report import build_excel_report

# Hệ số phát thải lưới điện Việt Nam năm 2023 (tCO2/MWh). Chỉ để tham khảo:
# người dùng cần nhập hệ số mới nhất do cơ quan có thẩm quyền công bố.
REFERENCE_GRID_EF = 0.6592

FUEL_OPTIONS = {f"{p.label} ({p.unit})": fuel for fuel, p in FUELS.items()}
COMBUSTION_OPTIONS = {"Di động": CombustionType.MOBILE, "Cố định": CombustionType.STATIONARY}
LEVEL_OPTIONS = {
    "Dưới 200 m (hệ số thấp)": EmissionFactorLevel.LOW,
    "Từ 200 đến 400 m (hệ số trung bình)": EmissionFactorLevel.AVERAGE,
    "Trên 400 m (hệ số cao)": EmissionFactorLevel.HIGH,
}
TIER_OPTIONS = {
    "Tier 1: hệ số mặc định IPCC": MethaneTier.TIER1,
    "Tier 2: hệ số riêng của mỏ": MethaneTier.TIER2,
    "Tier 3: số đo thực tế": MethaneTier.TIER3,
}
UNDERGROUND = MiningMethod.UNDERGROUND


def fmt(value: float, decimals: int = 0) -> str:
    """Định dạng số kiểu Việt Nam: dấu chấm phân cách hàng nghìn, dấu phẩy thập phân."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "\0").replace(".", ",").replace("\0", ".")


st.set_page_config(page_title="Kiểm kê KNK mỏ than hầm lò", page_icon="⛏️", layout="wide")
st.title("Kiểm kê khí nhà kính - mỏ than hầm lò")
st.caption("Tính phát thải theo IPCC 2006 và GHG Protocol; xuất báo cáo ra tệp Excel.")

with st.sidebar:
    st.header("Thông tin cơ sở")
    facility_name = st.text_input("Tên cơ sở", key="facility_name")
    address = st.text_input("Địa chỉ", key="address")
    reporting_year = st.number_input(
        "Năm kiểm kê", min_value=2000, max_value=2100, value=date.today().year - 1, step=1
    )
    prepared_by = st.text_input("Người lập", key="prepared_by")
    gwp = st.selectbox(
        "Bộ hệ số GWP",
        ["AR5", "AR6", "AR4"],
        help="Báo cáo theo khung minh bạch của Thỏa thuận Paris dùng AR5.",
    )

tab_methane, tab_fuel, tab_power, tab_explosive, tab_result = st.tabs(
    ["1. Sản lượng & khí mê-tan", "2. Nhiên liệu", "3. Điện năng", "4. Vật liệu nổ", "Kết quả"]
)

with tab_methane:
    production = st.number_input(
        "Sản lượng than nguyên khai (tấn)",
        min_value=0.0,
        step=10_000.0,
        format="%.0f",
        key="production",
    )
    tier = TIER_OPTIONS[
        st.radio("Cấp độ tính khí mê-tan", list(TIER_OPTIONS), horizontal=True, key="tier")
    ]
    level = EmissionFactorLevel.AVERAGE
    mining_ef = post_mining_ef = measured_mining_m3 = None
    if tier is MethaneTier.TIER1:
        level = LEVEL_OPTIONS[
            st.selectbox("Độ sâu khai thác", list(LEVEL_OPTIONS), index=1, key="level")
        ]
        st.caption(
            f"Hệ số áp dụng: {fmt(TIER1_MINING_EF[UNDERGROUND][level], 1)} m³/tấn khi khai thác, "
            f"{fmt(TIER1_POST_MINING_EF[UNDERGROUND][level], 1)} m³/tấn sau khai thác "
            "(IPCC 2006)."
        )
    elif tier is MethaneTier.TIER2:
        col1, col2 = st.columns(2)
        mining_ef = col1.number_input(
            "Hệ số CH4 khai thác (m³/tấn)", min_value=0.0, value=18.0, key="mining_ef"
        )
        post_mining_ef = col2.number_input(
            "Hệ số CH4 sau khai thác (m³/tấn)", min_value=0.0, value=2.5, key="post_mining_ef"
        )
    else:
        col1, col2 = st.columns(2)
        measured_mining_m3 = col1.number_input(
            "Thể tích CH4 đo được trong năm (m³)",
            min_value=0.0,
            step=10_000.0,
            format="%.0f",
            help="Tổng CH4 trong khí thông gió và hệ thống tháo khí mỏ.",
            key="measured_mining_m3",
        )
        post_mining_ef = col2.number_input(
            "Hệ số CH4 sau khai thác (m³/tấn)",
            min_value=0.0,
            value=2.5,
            help="Không đo trực tiếp được; mặc định lấy hệ số trung bình của IPCC.",
            key="post_mining_ef",
        )
    recovered_m3 = st.number_input(
        "CH4 thu hồi và đốt tại mỏ (m³)",
        min_value=0.0,
        step=1_000.0,
        format="%.0f",
        help="Được trừ khỏi phát thải CH4; CO2 sinh ra khi đốt được tính riêng.",
        key="recovered_m3",
    )

with tab_fuel:
    st.write("Nhập lượng nhiên liệu tiêu thụ trong năm. Có thể thêm hoặc xóa dòng.")
    fuel_table = st.data_editor(
        pd.DataFrame(
            {
                "Nhiên liệu": ["Dầu diesel (lít)", "Dầu diesel (lít)"],
                "Loại nguồn": ["Di động", "Cố định"],
                "Số lượng": [0.0, 0.0],
            }
        ),
        num_rows="dynamic",
        column_config={
            "Nhiên liệu": st.column_config.SelectboxColumn(
                options=list(FUEL_OPTIONS), required=True
            ),
            "Loại nguồn": st.column_config.SelectboxColumn(
                options=list(COMBUSTION_OPTIONS), required=True
            ),
            "Số lượng": st.column_config.NumberColumn(min_value=0.0, required=True),
        },
        key="fuels",
    )
    st.caption(
        "Di động: xe vận tải, máy xúc, máy khoan... Cố định: máy phát điện, lò hơi. "
        "Dầu FO và LPG chỉ áp dụng cho nguồn cố định."
    )
    with st.expander("Khối lượng riêng của nhiên liệu tính theo lít"):
        densities = {
            fuel: st.number_input(
                f"{props.label} (kg/lít)",
                min_value=0.01,
                value=props.density_kg_per_l,
                key=f"density_{fuel.value}",
            )
            for fuel, props in FUELS.items()
            if props.density_kg_per_l
        }

with tab_power:
    electricity_kwh = st.number_input(
        "Điện năng mua từ lưới trong năm (kWh)",
        min_value=0.0,
        step=10_000.0,
        format="%.0f",
        key="electricity_kwh",
    )
    grid_ef = st.number_input(
        "Hệ số phát thải lưới điện (tCO2/MWh)",
        min_value=0.0,
        value=REFERENCE_GRID_EF,
        format="%.4f",
        key="grid_ef",
    )
    st.caption(
        f"Giá trị mặc định {fmt(REFERENCE_GRID_EF, 4)} là hệ số năm 2023, chỉ để tham khảo. "
        "Hãy nhập hệ số mới nhất do Bộ Nông nghiệp và Môi trường công bố cho năm kiểm kê."
    )

with tab_explosive:
    explosives_kg = st.number_input(
        "Khối lượng thuốc nổ sử dụng trong năm (kg)",
        min_value=0.0,
        step=100.0,
        format="%.0f",
        key="explosives_kg",
    )
    explosives_ef = st.number_input(
        "Hệ số phát thải thuốc nổ (tCO2/tấn thuốc nổ)",
        min_value=0.0,
        value=DEFAULT_EXPLOSIVE_EF,
        format="%.3f",
        key="explosives_ef",
    )
    st.caption(
        "Giá trị mặc định là ước tính cho thuốc nổ ANFO. "
        "Nên thay bằng hệ số theo thành phần thuốc nổ thực tế của mỏ."
    )

fuels = [
    FuelUse(FUEL_OPTIONS[row["Nhiên liệu"]], COMBUSTION_OPTIONS[row["Loại nguồn"]], row["Số lượng"])
    for row in fuel_table.dropna().to_dict("records")
]
inventory_input = InventoryInput(
    facility_name=facility_name,
    address=address,
    reporting_year=int(reporting_year),
    prepared_by=prepared_by,
    gwp=gwp,
    coal_production_t=production,
    methane_tier=tier,
    methane_level=level,
    mining_ef=mining_ef,
    post_mining_ef=post_mining_ef,
    measured_mining_m3=measured_mining_m3,
    recovered_combusted_m3=recovered_m3,
    fuels=fuels,
    densities_kg_per_l=densities,
    electricity_kwh=electricity_kwh,
    grid_ef_t_per_mwh=grid_ef,
    explosives_kg=explosives_kg,
    explosives_ef_t_per_t=explosives_ef,
)

with tab_result:
    try:
        result = compute_inventory(inventory_input)
    except ValueError as error:
        st.error(f"Số liệu chưa hợp lệ: {error}")
        st.stop()

    intensity = result.intensity_kg_per_t
    cols = st.columns(4)
    cols[0].metric("Tổng phát thải (tCO2e)", fmt(result.total_co2e_t, 1))
    cols[1].metric("Scope 1 (tCO2e)", fmt(result.scope_co2e_t(1), 1))
    cols[2].metric("Scope 2 (tCO2e)", fmt(result.scope_co2e_t(2), 1))
    cols[3].metric("Cường độ (kgCO2e/tấn than)", "-" if intensity is None else fmt(intensity, 1))

    total = result.total_co2e_t
    table = pd.DataFrame(
        [
            {
                "Phạm vi": f"Scope {line.scope}",
                "Nguồn phát thải": line.source,
                "CO2 (tấn)": line.gases.co2_t,
                "CH4 (tấn)": line.gases.ch4_t,
                "N2O (tấn)": line.gases.n2o_t,
                "tCO2e": line.gases.co2e_t(gwp),
                "Tỷ trọng (%)": round(line.gases.co2e_t(gwp) / total * 100, 1) if total else 0.0,
            }
            for line in result.lines
        ]
    )
    number = st.column_config.NumberColumn(format="localized")
    st.dataframe(
        table,
        hide_index=True,
        column_config={
            col: number for col in table.columns if col not in ("Phạm vi", "Nguồn phát thải")
        },
    )

    st.download_button(
        "Tải báo cáo Excel",
        data=build_excel_report(inventory_input, result),
        file_name=f"kiem-ke-KNK-{int(reporting_year)}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
