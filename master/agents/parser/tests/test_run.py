import os
import sys

# Thêm đường dẫn thư mục parse_backend vào sys.path để test script chạy
current_dir = os.path.dirname(os.path.abspath(__file__))
parser_dir = os.path.dirname(current_dir)
backend_dir = os.path.join(parser_dir, "parse_backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from parser_agent import ParserAgent

def find_test_file() -> str | None:
    """Tự động tìm file test trong thư mục parser (thư mục cha)."""
    parser_dir = os.path.dirname(current_dir)
    
    # Ưu tiên PDF, rồi tới ảnh
    candidates = [
        "test_exam.pdf",
        "test_exam.png",
        "test_exam.jpg",
        "test_exam.jpeg",
    ]
    
    for name in candidates:
        path = os.path.join(parser_dir, name)
        if os.path.exists(path):
            return path
    
    # Cũng tìm trong thư mục tests
    for name in candidates:
        path = os.path.join(current_dir, name)
        if os.path.exists(path):
            return path
    
    return None

if __name__ == "__main__":
    # Xác định file input
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        # Nếu path gốc không tồn tại, thử tìm trong thư mục tests/
        if not os.path.exists(file_path):
            alt_path = os.path.join(current_dir, os.path.basename(file_path))
            if os.path.exists(alt_path):
                file_path = alt_path
            else:
                # Thử tìm trong thư mục parser root
                alt_path2 = os.path.join(parser_dir, os.path.basename(file_path))
                if os.path.exists(alt_path2):
                    file_path = alt_path2
    else:
        file_path = find_test_file()

    if not file_path or not os.path.exists(file_path):
        print("Không tìm thấy file đề thi!")
        sys.exit(1)

    # 1. Khởi tạo mảng lưu trữ (Thư mục default: parsed_results)
    parser = ParserAgent(output_dir="parsed_results")
    
    try:
        # 2. Xử lý tự động A-Z
        result_path = parser.process(file_path)

        if result_path:
            print(f"THÀNH CÔNG: Dữ liệu JSON đã được trích xuất hoàn chỉnh tại: {result_path}")
        else:
            print("\Pipeline thất bại — không có kết quả đầu ra.")
            sys.exit(1)

    except Exception as e:
        print(f"\nCó lỗi xảy ra trong quá trình xử lý:")
        import traceback
        traceback.print_exc()
        sys.exit(1)
