import os
import sys


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(CURRENT_DIR, "parse_backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


from parser_agent import ParserAgent


def find_input_file() -> str | None:
    candidates = [
        "test_exam.pdf",
        "test_exam.png",
        "test_exam.jpg",
        "test_exam.jpeg",
    ]

    search_dirs = [
        CURRENT_DIR,
        os.path.join(CURRENT_DIR, "tests"),
    ]

    for search_dir in search_dirs:
        for name in candidates:
            path = os.path.join(search_dir, name)
            if os.path.exists(path):
                return path

    return None


def resolve_input_path(raw_path: str) -> str | None:
    if os.path.exists(raw_path):
        return raw_path

    for base_dir in [CURRENT_DIR, os.path.join(CURRENT_DIR, "tests")]:
        candidate = os.path.join(base_dir, os.path.basename(raw_path))
        if os.path.exists(candidate):
            return candidate

    return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = resolve_input_path(sys.argv[1])
    else:
        file_path = find_input_file()

    if not file_path:
        print("[Pipeline] Input file not found")
        sys.exit(1)

    parser = ParserAgent(output_dir="parsed_results")
    if not parser.mongo_client.is_configured():
        print("[Pipeline] MongoDB config is missing")
        sys.exit(1)

    try:
        result_path = parser.process(file_path, push_to_mongo=True)
        if not result_path:
            print("[Pipeline] No output generated")
            sys.exit(1)

        print(f"[Pipeline] Done {result_path}")
    except Exception:
        import traceback

        print("[Pipeline] Execution failed")
        traceback.print_exc()
        sys.exit(1)
