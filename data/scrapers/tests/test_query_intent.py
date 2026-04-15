from exam_scraper.config import Settings
from exam_scraper.utils.query_intent import QueryIntentParser


def test_query_intent_parser_subject_grade_exam_type():
    parser = QueryIntentParser(Settings().detectors.intent)
    intent = parser.parse("de thi hoc ky 2 mon vat ly lop 11")

    assert intent.subject == "ly"
    assert intent.grade == "11"
    assert intent.exam_type == "hk2"


def test_query_intent_parser_empty_query():
    parser = QueryIntentParser(Settings().detectors.intent)
    intent = parser.parse(None)

    assert intent.subject is None
    assert intent.grade is None
    assert intent.exam_type is None
