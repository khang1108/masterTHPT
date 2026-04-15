import re
import unicodedata


QUESTION_START_PATTERN = re.compile(r"(?i)(cau|bai)\s*(\d+)[\.:\s]")
QUESTION_LINE_PATTERN = re.compile(r"(?i)^\s*(?:\[[^\]]+\]\s*)?(cau|bai)\s*(\d+)\b")


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text or "")
    normalized = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    normalized = normalized.replace("đ", "d").replace("Đ", "D")
    return normalized.lower()


def _extract_question_index_hint(text: str) -> int | None:
    normalized_text = _normalize_text(text)
    for line in normalized_text.splitlines():
        match = QUESTION_LINE_PATTERN.search(line)
        if not match:
            continue

        try:
            return int(match.group(2))
        except (TypeError, ValueError):
            return None

    return None


def _new_question(raw_text: str, bbox: list, question_index_hint: int | None) -> dict:
    return {
        "raw_text": raw_text,
        "bbox": list(bbox),
        "min_y": bbox[1],
        "max_y": bbox[3],
        "question_index_hint": question_index_hint,
        "image_path": None,
        "image_url": None,
    }


def _fill_missing_question_indexes(questions: list[dict]) -> None:
    used_indexes = {
        question["question_index_hint"]
        for question in questions
        if isinstance(question.get("question_index_hint"), int)
    }

    for index, question in enumerate(questions):
        if question.get("question_index_hint") is not None:
            continue

        previous_index = None
        next_index = None

        for previous_question in reversed(questions[:index]):
            previous_hint = previous_question.get("question_index_hint")
            if isinstance(previous_hint, int):
                previous_index = previous_hint
                break

        for next_question in questions[index + 1:]:
            next_hint = next_question.get("question_index_hint")
            if isinstance(next_hint, int):
                next_index = next_hint
                break

        candidate = None
        if previous_index is None and isinstance(next_index, int) and next_index > 1:
            candidate = next_index - 1
        elif isinstance(previous_index, int) and next_index is None:
            candidate = previous_index + 1
        elif (
            isinstance(previous_index, int)
            and isinstance(next_index, int)
            and next_index - previous_index == 2
        ):
            candidate = previous_index + 1

        if candidate and candidate not in used_indexes:
            question["question_index_hint"] = candidate
            used_indexes.add(candidate)


def _pick_best_question_for_asset(asset_bbox: list, questions: list[dict]) -> dict | None:
    if not asset_bbox or len(asset_bbox) != 4 or not questions:
        return None

    asset_left, asset_top, asset_right, asset_bottom = asset_bbox
    asset_center_y = (asset_top + asset_bottom) / 2.0
    best_question = None
    best_score = None

    for question in questions:
        question_left, question_top, question_right, question_bottom = question["bbox"]
        question_center_y = (question_top + question_bottom) / 2.0

        vertical_overlap = max(
            0.0,
            min(asset_bottom, question_bottom) - max(asset_top, question_top),
        )
        horizontal_overlap = max(
            0.0,
            min(asset_right, question_right) - max(asset_left, question_left),
        )
        contains_center = question_top <= asset_center_y <= question_bottom
        vertical_gap = 0.0 if contains_center or vertical_overlap > 0 else min(
            abs(asset_top - question_bottom),
            abs(asset_bottom - question_top),
            abs(asset_center_y - question_center_y),
        )

        score = (
            0 if contains_center else 1,
            -vertical_overlap,
            -horizontal_overlap,
            vertical_gap,
            abs(asset_center_y - question_center_y),
        )

        if best_score is None or score < best_score:
            best_score = score
            best_question = question

    return best_question


def group_blocks_into_questions(parsing_blocks: list, page_visual_crops: dict) -> list[dict]:
    """Group OCR blocks and attach one matched visual crop per question."""
    text_blocks = [
        block
        for block in parsing_blocks
        if block.get("label", "") not in ("figure", "figure_image", "image")
    ]

    questions: list[dict] = []
    current_question = None

    for block in text_blocks:
        content = block.get("content", "").strip()
        bbox = block.get("bbox", [0, 0, 0, 0])
        label = block.get("label", "text")
        normalized_content = _normalize_text(content)
        match = QUESTION_START_PATTERN.search(normalized_content)
        question_index_hint = _extract_question_index_hint(f"[{label}] {content}")

        if match and match.start() < 15:
            if current_question:
                questions.append(current_question)

            current_question = _new_question(
                f"[{label}] {content}",
                list(bbox),
                question_index_hint,
            )
            continue

        if not current_question:
            current_question = _new_question("", list(bbox), question_index_hint)

        current_question["raw_text"] = (
            f"{current_question['raw_text']}\n[{label}] {content}"
            if current_question["raw_text"]
            else f"[{label}] {content}"
        )
        current_question["bbox"][0] = min(current_question["bbox"][0], bbox[0])
        current_question["bbox"][1] = min(current_question["bbox"][1], bbox[1])
        current_question["bbox"][2] = max(current_question["bbox"][2], bbox[2])
        current_question["bbox"][3] = max(current_question["bbox"][3], bbox[3])
        current_question["min_y"] = min(current_question["min_y"], bbox[1])
        current_question["max_y"] = max(current_question["max_y"], bbox[3])
        if current_question["question_index_hint"] is None and question_index_hint is not None:
            current_question["question_index_hint"] = question_index_hint

    if current_question:
        questions.append(current_question)

    _fill_missing_question_indexes(questions)

    for asset in page_visual_crops.values():
        if not asset.get("bbox"):
            continue

        best_question = _pick_best_question_for_asset(asset["bbox"], questions)
        if best_question and not best_question["image_url"]:
            best_question["image_path"] = asset["abs_path"]
            best_question["image_url"] = asset["web_url"]
            best_question["raw_text"] += f"\n[FIGURE_URL: {asset['web_url']}]"

    return questions
