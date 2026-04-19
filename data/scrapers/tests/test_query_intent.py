from exam_scraper.config import Settings
from exam_scraper.core import QueryIntentParser


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


def test_query_intent_parser_aliases():
    parser = QueryIntentParser(Settings().detectors.intent)
    intent = parser.parse("lay de gk1 toan lop 12 de thi thptqg")

    assert intent.subject == "toan"
    assert intent.grade == "12"
    assert intent.exam_type == "thptqg"


def test_query_intent_parser_detects_hsg_and_khao_sat():
    parser = QueryIntentParser(Settings().detectors.intent)

    hsg_intent = parser.parse("lay de hoc sinh gioi toan lop 10")
    khao_sat_intent = parser.parse("lay de kscl toan lop 10")

    assert hsg_intent.exam_type == "hsg"
    assert khao_sat_intent.exam_type == "khao_sat"
