# carbon-pricing

Bộ công cụ mô hình hóa và phân tích định giá carbon: tính chi phí phát thải
theo một mức giá carbon và dự báo lộ trình giá carbon theo thời gian.

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

## Bắt đầu nhanh

```python
from carbon_pricing import carbon_cost, price_path

# Chi phí của 1.250 tCO2e với giá 85 USD/tấn
carbon_cost(1250, 85.0)  # -> 106250.0

# Giá khởi điểm 50 USD/tấn, tăng 5% mỗi năm trong 5 năm
price_path(50.0, growth_rate=0.05, years=5)
# -> [50.0, 52.5, 55.125, 57.88125, 60.7753125]
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
src/carbon_pricing/   # mã nguồn thư viện
tests/                # bộ kiểm thử pytest
.github/workflows/    # CI (lint + test mỗi lần push và pull request)
```

## Giấy phép

MIT, xem [LICENSE](LICENSE).
