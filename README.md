# Tính toán dấu chân carbon cho mỏ than

Ứng dụng tính toán dấu chân carbon (carbon footprint) cho hoạt động khai thác
mỏ than. Ứng dụng định lượng lượng phát thải khí nhà kính (KNK) của mỏ trong
một kỳ báo cáo, quy đổi ra tấn CO2 tương đương (tCO2e), phân theo từng nguồn
phát thải và từng phạm vi (Scope 1, 2, 3).

Ứng dụng có giao diện web để kỹ sư mỏ nhập số liệu và xuất kết quả ra tệp
Excel, phục vụ báo cáo kiểm kê KNK gửi cơ quan quản lý. Phiên bản hiện tại
dành cho **mỏ than hầm lò**.

## Mục tiêu

- Tính tổng phát thải KNK của một mỏ than (hầm lò hoặc lộ thiên) theo năm.
- Tính cường độ phát thải: kgCO2e trên mỗi tấn than nguyên khai.
- Chỉ ra các nguồn phát thải lớn nhất để ưu tiên giải pháp giảm phát thải.
- Hỗ trợ lập báo cáo kiểm kê KNK cấp cơ sở.

## Phạm vi tính toán

Phân loại theo GHG Protocol:

**Scope 1: phát thải trực tiếp**

- Khí mê-tan (CH4) thoát ra trong quá trình khai thác hầm lò và lộ thiên.
- CH4 phát thải sau khai thác (sàng tuyển, vận chuyển, lưu kho than).
- Đốt nhiên liệu của thiết bị di động: máy xúc, ô tô tải, máy khoan, máy gạt.
- Đốt nhiên liệu tại nguồn cố định: máy phát điện, lò hơi.
- Sử dụng vật liệu nổ.
- Giảm trừ lượng CH4 được thu hồi để sử dụng hoặc đốt bỏ.

**Scope 2: phát thải gián tiếp từ năng lượng mua vào**

- Điện mua từ lưới cho quạt gió, bơm thoát nước, băng tải, nhà máy tuyển.

**Scope 3: phát thải gián tiếp khác (tùy chọn)**

- Vận chuyển than đến khách hàng.
- Vật tư đầu vào như thép, gỗ chống lò.

## Phương pháp luận

- **IPCC 2006 Guidelines** và bản **2019 Refinement**: Tập 2, Chương 4.1 cho
  phát thải từ khai thác và xử lý than; Chương 2 và 3 cho đốt nhiên liệu.
- **GHG Protocol Corporate Standard** để phân loại Scope 1, 2, 3.
- **Hệ số tiềm năng nóng lên toàn cầu (GWP)** theo các báo cáo đánh giá của
  IPCC (AR5, AR6), người dùng chọn được.
- **Hệ số phát thải lưới điện Việt Nam** theo số liệu do cơ quan quản lý nhà
  nước công bố hằng năm.

Ứng dụng hỗ trợ nhiều cấp độ chính xác:

- **Tier 1:** dùng hệ số phát thải mặc định của IPCC.
- **Tier 2:** dùng hệ số riêng của quốc gia hoặc của bể than.
- **Tier 3:** dùng số liệu đo thực tế tại mỏ, ví dụ lưu lượng và nồng độ CH4
  trong khí thông gió.

## Dữ liệu đầu vào (dự kiến)

| Nhóm dữ liệu | Ví dụ | Đơn vị |
| --- | --- | --- |
| Sản lượng | Than nguyên khai theo phương pháp khai thác | tấn |
| Khí mỏ | Lưu lượng, nồng độ CH4 thông gió; lượng CH4 thu hồi | m³, % |
| Nhiên liệu | Dầu diesel, xăng, khí đốt tiêu thụ | lít, tấn |
| Điện năng | Điện mua từ lưới | MWh |
| Vật liệu nổ | Khối lượng thuốc nổ sử dụng | tấn |

## Kết quả đầu ra (dự kiến)

- Tổng phát thải (tCO2e), phân theo scope, theo nguồn và theo loại khí
  (CO2, CH4, N2O).
- Cường độ phát thải (kgCO2e/tấn than).
- Báo cáo xuất ra tệp CSV hoặc Excel.

## Lộ trình phát triển

- [x] Mô hình dữ liệu đầu vào của mỏ và kỳ báo cáo
- [x] Phát thải CH4 từ khai thác hầm lò và lộ thiên (Tier 1, 2, 3)
- [x] Phát thải từ đốt nhiên liệu (di động và cố định)
- [x] Phát thải từ điện năng tiêu thụ (Scope 2)
- [x] Phát thải từ vật liệu nổ
- [x] Tổng hợp kết quả và cường độ phát thải
- [x] Xuất báo cáo Excel
- [ ] Nhập số liệu từ tệp Excel
- [x] Giao diện web nhập số liệu
- [ ] Triển khai ứng dụng lên máy chủ cho kỹ sư dùng chung
- [ ] Đối chiếu với biểu mẫu báo cáo kiểm kê KNK theo quy định hiện hành

## Sử dụng ứng dụng web

Sau khi [cài đặt](#cài-đặt), chạy:

```bash
streamlit run app.py
```

Trình duyệt sẽ mở địa chỉ http://localhost:8501. Nhập số liệu theo từng thẻ:

1. **Sản lượng & khí mê-tan:** sản lượng than, cấp độ tính (Tier 1, 2, 3),
   lượng CH4 thu hồi và đốt tại mỏ.
2. **Nhiên liệu:** bảng nhiên liệu tiêu thụ (diesel, xăng, dầu FO, LPG) theo
   nguồn di động hoặc cố định.
3. **Điện năng:** điện mua từ lưới (kWh) và hệ số phát thải lưới điện.
4. **Vật liệu nổ:** khối lượng thuốc nổ (kg) và hệ số phát thải.
5. **Kết quả:** tổng phát thải, Scope 1, Scope 2, cường độ phát thải, bảng chi
   tiết theo nguồn và nút **Tải báo cáo Excel**.

Tệp Excel gồm 4 trang: Thông tin chung, Kết quả, Số liệu đầu vào và Hệ số phát
thải (ghi rõ giá trị và nguồn của từng hệ số).

> **Lưu ý về hệ số:** hệ số lưới điện mặc định (0,6592 tCO2/MWh, năm 2023) và
> hệ số thuốc nổ mặc định (0,17 tCO2/tấn, ước tính cho ANFO) chỉ để tham khảo.
> Hãy nhập hệ số chính thức mới nhất và hệ số theo loại thuốc nổ thực tế của mỏ.

## Dùng như thư viện Python

```python
from coal_mine_footprint.combustion import CombustionType, Fuel
from coal_mine_footprint.inventory import FuelUse, InventoryInput, compute_inventory

result = compute_inventory(
    InventoryInput(
        coal_production_t=1_000_000,
        fuels=[FuelUse(Fuel.DIESEL, CombustionType.MOBILE, 500_000)],  # lít
        electricity_kwh=40_000_000,
        grid_ef_t_per_mwh=0.6592,
    )
)
result.total_co2e_t  # tổng phát thải (tCO2e, GWP AR5)
result.intensity_kg_per_t  # kgCO2e / tấn than
```

## Yêu cầu

- Python 3.10 trở lên

## Cài đặt

```bash
git clone https://github.com/pqhuy2013/coal-mine-carbon-footprint.git
cd coal-mine-carbon-footprint
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Phát triển

```bash
ruff check .   # kiểm tra lỗi code (lint)
ruff format .  # định dạng code
pytest         # chạy kiểm thử
```

Có thể cài git hook để các bước kiểm tra tự chạy mỗi lần commit:

```bash
pre-commit install
```

## Cấu trúc dự án

```
app.py                     # giao diện web (Streamlit)
src/coal_mine_footprint/   # thư viện tính toán và xuất báo cáo
tests/                     # bộ kiểm thử pytest
.github/workflows/         # CI (lint + test mỗi lần push và pull request)
```

## Giấy phép

MIT, xem [LICENSE](LICENSE).
