# Tính toán dấu chân carbon cho mỏ than

Ứng dụng tính toán dấu chân carbon (carbon footprint) cho hoạt động khai thác
mỏ than. Ứng dụng định lượng lượng phát thải khí nhà kính (KNK) của mỏ trong
một kỳ báo cáo, quy đổi ra tấn CO2 tương đương (tCO2e), phân theo từng nguồn
phát thải và từng phạm vi (Scope 1, 2, 3).

> **Trạng thái:** đang ở giai đoạn khởi tạo. Các mô-đun tính toán sẽ được xây
> dựng dần theo [lộ trình](#lộ-trình-phát-triển) bên dưới.

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

- [ ] Mô hình dữ liệu đầu vào của mỏ và kỳ báo cáo
- [x] Phát thải CH4 từ khai thác hầm lò và lộ thiên (Tier 1, 2, 3)
- [ ] Phát thải từ đốt nhiên liệu (di động và cố định)
- [ ] Phát thải từ điện năng tiêu thụ (Scope 2)
- [ ] Phát thải từ vật liệu nổ
- [ ] Tổng hợp kết quả và cường độ phát thải
- [ ] Nhập dữ liệu từ tệp CSV/Excel và xuất báo cáo
- [ ] Giao diện người dùng

## Ví dụ sử dụng

Tính phát thải mê-tan của mỏ hầm lò sản xuất 1 triệu tấn than/năm, dùng hệ số
mặc định Tier 1 của IPCC:

```python
from coal_mine_footprint import MiningMethod, fugitive_methane

ch4 = fugitive_methane(1_000_000, MiningMethod.UNDERGROUND)
ch4.net_m3  # -> 20500000.0 (m³ CH4)
ch4.ch4_tonnes  # -> 13735.0 (tấn CH4)
ch4.co2e_tonnes("AR6")  # -> 409303.0 (tCO2e)
```

Dùng hệ số riêng của mỏ (Tier 2) và trừ lượng CH4 thu hồi:

```python
fugitive_methane(
    1_000_000,
    MiningMethod.UNDERGROUND,
    mining_ef=12.0,  # m³ CH4 / tấn
    post_mining_ef=1.5,
    recovered_m3=2_000_000,
)
```

## Yêu cầu

- Python 3.10 trở lên

## Cài đặt

```bash
git clone https://github.com/pqhuy2013/carbon-pricing.git
cd carbon-pricing
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
src/coal_mine_footprint/   # mã nguồn ứng dụng
tests/                     # bộ kiểm thử pytest
.github/workflows/         # CI (lint + test mỗi lần push và pull request)
```

## Giấy phép

MIT, xem [LICENSE](LICENSE).
