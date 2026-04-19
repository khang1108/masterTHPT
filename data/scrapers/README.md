# ToanMath-Only Exam Scraper

Tool này crawl PDF đề thi từ `toanmath.com` bằng Playwright.

## Mục tiêu

- Duyệt sâu trong `toanmath.com` để tìm trang đề phù hợp.
- Detect nút/link tải PDF bằng DOM + network signal + click flow.
- Lưu PDF theo đúng contract mới:
  - `storage/pdfs/<subject>/<grade_dir>/...`
  - `storage/pdfs/others/...` nếu thiếu `subject` hoặc `grade`
- Giữ metadata nội bộ bằng SQLite và dedup theo URL/hash/header.

## Cấu trúc chính

```text
src/exam_scraper/
├── __init__.py
├── cli.py
├── config.py
├── core.py
├── pdf_splitter.py
└── tool_api.py
```

## Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Chạy crawl

Đứng ở root project:

```bash
cd "/home/nagahuy/Documents/Hackathon 2026/masterTHPT/data/scrapers"
```

Kích hoạt môi trường:

```bash
conda activate exam_scraper
```

Lệnh tối thiểu:

```bash
PYTHONPATH=src python -m exam_scraper.cli crawl --start-url https://toanmath.com --limit 10
```

Các option hiện có:

- `--start-url`: URL bắt đầu crawl, bắt buộc thuộc `toanmath.com`
- `--limit`: số PDF tối đa cần tải
- `--subject`: lọc môn, ví dụ `toan`
- `--grade`: lọc lớp, ví dụ `10`, `11`, `12`, `thpt`
- `--exam-type`: lọc đợt thi, ví dụ `hk1`, `hk2`, `giua_hk1`, `giua_hk2`, `khao_sat`, `hsg`, `thptqg`
- `--query`: intent tự nhiên để resolve `subject/grade/exam_type`
- `--force`: xóa URL dedup cache trước khi crawl

Ví dụ theo từng option:

Chỉ định URL và limit:

```bash
PYTHONPATH=src python -m exam_scraper.cli crawl \
  --start-url "https://toanmath.com/chuyen-muc/de-thi-hoc-ky-1-mon-toan.html" \
  --limit 5
```

Lọc theo lớp:

```bash
PYTHONPATH=src python -m exam_scraper.cli crawl \
  --start-url "https://toanmath.com" \
  --grade 12 \
  --limit 5
```

Lọc theo môn:

```bash
PYTHONPATH=src python -m exam_scraper.cli crawl \
  --start-url "https://toanmath.com" \
  --subject toan \
  --limit 5
```

Lọc theo đợt thi:

```bash
PYTHONPATH=src python -m exam_scraper.cli crawl \
  --start-url "https://toanmath.com" \
  --exam-type hk1 \
  --limit 5
```

Lọc theo lớp + đợt thi:

```bash
PYTHONPATH=src python -m exam_scraper.cli crawl \
  --start-url "https://toanmath.com" \
  --grade 12 \
  --exam-type hk1 \
  --limit 5
```

Lọc theo môn + lớp + đợt thi:

```bash
PYTHONPATH=src python -m exam_scraper.cli crawl \
  --start-url "https://toanmath.com" \
  --subject toan \
  --grade 12 \
  --exam-type hk1 \
  --limit 5
```

Dùng query tự nhiên:

```bash
PYTHONPATH=src python -m exam_scraper.cli crawl \
  --start-url "https://toanmath.com" \
  --query "de hk1 mon toan lop 12" \
  --limit 5

Dùng `--force` để bỏ qua URL cache:

```bash
PYTHONPATH=src python -m exam_scraper.cli crawl \
  --start-url "https://toanmath.com" \
  --query "de hk1 mon toan lop 12" \
  --limit 5 \
  --force
```

Ví dụ cho từng exam type:

```bash
PYTHONPATH=src python -m exam_scraper.cli crawl --start-url "https://toanmath.com" --grade 12 --exam-type giua_hk1 --limit 5
PYTHONPATH=src python -m exam_scraper.cli crawl --start-url "https://toanmath.com" --grade 12 --exam-type hk1 --limit 5
PYTHONPATH=src python -m exam_scraper.cli crawl --start-url "https://toanmath.com" --grade 12 --exam-type giua_hk2 --limit 5
PYTHONPATH=src python -m exam_scraper.cli crawl --start-url "https://toanmath.com" --grade 12 --exam-type hk2 --limit 5
PYTHONPATH=src python -m exam_scraper.cli crawl --start-url "https://toanmath.com" --grade 12 --exam-type khao_sat --limit 5
PYTHONPATH=src python -m exam_scraper.cli crawl --start-url "https://toanmath.com" --grade 12 --exam-type hsg --limit 5
PYTHONPATH=src python -m exam_scraper.cli crawl --start-url "https://toanmath.com" --grade thpt --exam-type thptqg --limit 5
```

`--start-url` chỉ chấp nhận URL thuộc `toanmath.com`.

Các URL trực tiếp nên dùng khi đã biết lớp và loại đề:

```bash
PYTHONPATH=src python -m exam_scraper.cli crawl --start-url "https://toanmath.com/de-thi-giua-hk1-toan-10" --grade 10 --exam-type giua_hk1 --limit 5
PYTHONPATH=src python -m exam_scraper.cli crawl --start-url "https://toanmath.com/de-thi-hk1-toan-10" --grade 10 --exam-type hk1 --limit 5
PYTHONPATH=src python -m exam_scraper.cli crawl --start-url "https://toanmath.com/khao-sat-chat-luong-toan-10" --grade 10 --exam-type khao_sat --limit 5
PYTHONPATH=src python -m exam_scraper.cli crawl --start-url "https://toanmath.com/de-thi-hsg-toan-10" --grade 10 --exam-type hsg --limit 5
```

## Vì sao `--limit 5` có thể chỉ tải được 1 file

`--limit` là trần trên, không phải cam kết sẽ luôn tải đủ 5 file.

Crawler sẽ dừng sớm khi gặp một trong các trường hợp này:

- `start_url` là một trang detail chỉ có đúng 1 đề; tải xong thì hết nhánh để đi tiếp
- Trang đã bị mark trong URL dedup cache từ run trước
- PDF mới phát hiện nhưng trùng file cũ theo header/hash nên bị bỏ qua
- Trang không khớp filter `subject`, `grade`, hoặc `exam_type`
- Trang có `year < 2024` nên bị skip theo `config.yaml`
- Không còn URL con hợp lệ trong domain để DFS tiếp

Lưu ý quan trọng về logic hiện tại:

- Nếu một page đã tải được 1 đề hợp lệ, crawler coi page đó đã xử lý xong và sẽ back ra
- Nó không cố tải thêm nhiều đề từ cùng một page
- Vì vậy nếu bạn bắt đầu từ một bài viết detail, thường kết quả chỉ là 1

Muốn tăng xác suất đủ 5 file, nên bắt đầu từ category/listing URL thay vì detail URL. Ví dụ:

```bash
PYTHONPATH=src python -m exam_scraper.cli crawl \
  --start-url "https://toanmath.com/chuyen-muc/de-thi-hoc-ky-1-mon-toan.html" \
  --grade 12 \
  --exam-type hk1 \
  --limit 5 \
  --force
```

## Python Tool API

Manager khác có thể import và gọi tool trực tiếp:

```python
from exam_scraper import run_crawl_tool

result = run_crawl_tool(
    {
        "grade": "10",
        "exam_type": "khao_sat",
        "limit": 5,
    }
)
```

Hoặc lấy definition trước:

```python
from exam_scraper import get_crawl_tool_definition

tool_definition = get_crawl_tool_definition()
```

Agent chỉ cần chọn `grade`, `exam_type`, `limit`; tool sẽ tự build start URL trực tiếp:

```python
from exam_scraper import crawl_toanmath_by_tags

result = crawl_toanmath_by_tags(grade="10", exam_type="hsg", limit=5)
```

Khi gọi trực tiếp từ shell:

```bash
PYTHONPATH=src python - <<'PY'
from exam_scraper import run_crawl_tool

result = run_crawl_tool({"intent": "Lấy đề gk1 môn Toán lớp 11", "limit": 2})
print(result["resolved"])
PY
```

## Runtime output

- PDF: `storage/pdfs/`
- SQLite state: `storage/state/crawl_cache.db`
- Temp rollback files: `storage/state/.tmp_runs/`

## Cắt PDF Thủ Công

Có thể đưa trực tiếp một hoặc nhiều file PDF vào splitter mà không chạy crawler:

```bash
python src/exam_scraper/pdf_splitter.py "/path/to/de-thi.pdf"
```

Chạy nhiều file cùng lúc:

```bash
python src/exam_scraper/pdf_splitter.py "/path/to/de-1.pdf" "/path/to/de-2.pdf"
```

Output mặc định nằm cạnh từng file PDF gốc:

```text
de-thi.pdf
output/
├── de-thi_split.pdf
└── de-thi/
    ├── 1.png
    └── 2.png
```

## Test

```bash
PYTHONPATH=src python -m pytest -q
```
