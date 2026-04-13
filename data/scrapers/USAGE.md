# Hướng dẫn sử dụng `exam-scraper`

Tài liệu này mô tả CLI hiện tại sau khi migrate sang **Playwright full-flow** (listing/detail/detect click/download PDF).

## 1. Chuẩn bị môi trường

### Yêu cầu
- Python `>= 3.11`
- Linux/macOS shell (Windows dùng WSL hoặc PowerShell tương đương)

### Cài đặt nhanh
```bash
cd /path/to/exam-scraper
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
playwright install chromium
```

### Kiểm tra CLI
```bash
exam-scraper --help
```

## 2. Command chính

```bash
exam-scraper [COMMAND] [OPTIONS]
```

- `crawl`: crawl và tải PDF
- `stats`: xem thống kê DB
- `export`: xuất `batch_manifest.json` từ các document `pending`

## 3. Lệnh `crawl`

### Cú pháp
```bash
exam-scraper crawl --domain <domain> [OPTIONS]
```

### Options
- `--domain TEXT` (bắt buộc): domain cần crawl, ví dụ `toanmath.com`
- `--start-url TEXT`: URL bắt đầu crawl, mặc định `https://<domain>`
- `--grade TEXT`: lọc lớp (`10`, `11`, `12`, `thpt`)
- `--subject TEXT`: lọc môn (vd `toan`, `ly`, `van`, `anh`)
- `--exam-type TEXT`: lọc loại đề (`hk1`, `hk2`, `giua_hk1`, `thi_thu`, ...)
- `--query TEXT`: query tự nhiên để detect `subject/grade/exam_type`
- `--limit INTEGER`: số PDF tối đa tải về, mặc định `10`
- `--min-year INTEGER`: bỏ qua bài có năm nhỏ hơn giá trị này, mặc định `2022`
- `--force / --no-force`: khi `--force`, xóa dedup cache theo domain trước khi crawl
- `--tier TEXT`: giữ tương thích CLI cũ (không còn quyết định engine runtime)
- `--auto-discover`: nếu domain đầu tiên không tải được PDF nào, thử fallback domain
- Bộ cờ lọc môn:
  - `--toan`, `--ngu_van`, `--tieng_anh`, `--vat_ly`, `--hoa_hoc`, `--sinh_hoc`
  - `--lich_su`, `--dia_ly`, `--gdcd`, `--gdktpl`, `--tin_hoc`, `--cong_nghe`

### Rule ưu tiên filter
`Option tường minh > --query > detect tự động từ title/url trang detail`

Ví dụ:
- `--query "de thi hk1 toan lop 12"` + `--vat_ly` -> giữ `vat_ly`, bỏ subject từ query và log warning.

### Ví dụ chạy

Crawl nhanh 5 file:
```bash
exam-scraper crawl --domain toanmath.com --limit 5
```

Dùng query tự nhiên:
```bash
exam-scraper crawl \
  --domain thi247.com \
  --query "de thi hoc ky 2 mon vat ly lop 11" \
  --limit 20
```

Override query bằng option tường minh:
```bash
exam-scraper crawl \
  --domain doctailieu.com \
  --query "de thi hk1 mon toan lop 12" \
  --subject ly --grade 12 --exam-type hk1 \
  --limit 20
```

Bỏ dedup cache của domain và crawl lại:
```bash
exam-scraper crawl --domain toanmath.com --force --limit 10
```

## 4. Cơ chế Playwright detect link tải PDF

Luồng runtime:
1. Mở URL hiện tại bằng Playwright như người dùng thật.
2. Parse toàn bộ link con trên trang.
3. Chấm điểm link theo tag (môn/lớp/loại đề) và ưu tiên nhánh liên quan.
4. Duyệt theo **DFS (đi sâu trước, quay lại sau)**: đi sâu tối đa đến khi không còn link phù hợp, rồi backtrack.
5. Ở mỗi trang, detect/click candidate tải (bao gồm iframe PDF viewer) theo keyword scoring.
6. Bắt URL PDF từ `download event` + network request/response + URL embedded trong viewer.
7. Lọc URL rác (asset `.svg/.js/.css/...`) và validate PDF rồi mới ghi vào storage.

Keyword detect (positive/negative, weights) nằm trong `config.yaml`.

## 5. Fail-fast + rollback

Crawler chạy theo transaction cho mỗi run:
- Download vào file tạm `.part`.
- Validate bắt buộc: kích thước, magic bytes `%PDF-`, network/header signal khi cần.
- Nếu có lỗi trong run:
  - dừng ngay toàn bộ job,
  - rollback DB,
  - xóa toàn bộ file đã phát sinh trong run đó,
  - process trả mã lỗi non-zero.

Kết quả: không để lại file rác hoặc DB commit dở dang khi run thất bại.

## 6. Cấu hình detector trong `config.yaml`

```yaml
crawl:
  max_depth: 8
  max_pages: 500

detectors:
  max_click_attempts: 6
  network_wait_ms: 2500
  download_keywords:
    positive: ["tai", "tai ve", "download", "pdf", "xem de"]
    negative: ["dang nhap", "quang cao", "lien he"]
    weights:
      text: 3.0
      href: 4.0
      aria_label: 2.0
      title: 2.0
      class_name: 1.0
      element_id: 1.0
      nearby_text: 1.5
  intent:
    subjects: { toan: ["toan"], ly: ["vat ly", "ly"] }
    grades: { "10": ["lop 10"], "11": ["lop 11"], "12": ["lop 12"], thpt: ["thpt"] }
    exam_types: { hk1: ["hoc ky 1"], hk2: ["hoc ky 2"], thi_thu: ["thi thu"] }
```

## 7. Lệnh `stats`

```bash
exam-scraper stats
```

In ra:
- `Crawled URLs`: tổng số URL đã cache dedup
- `Stored Documents`: tổng số bản ghi PDF trong `exam_documents`

## 8. Lệnh `export`

```bash
exam-scraper export [--batch-name <ten_batch>]
```

Hành vi:
- Lấy document có `parse_status='pending'`
- Ghi file `data/batch_manifest.json`
- Update các bản ghi vừa export thành `parse_status='sent'`

## 9. Vị trí dữ liệu

- PDF: `storage/<domain>/lop-<grade>/<subject>/<exam_type>/*.pdf`
- SQLite: `data/crawl_cache.db`
- Manifest: `data/batch_manifest.json`

## 10. Kiểm thử

```bash
pytest -q
```
