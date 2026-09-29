import pytest

from journalport.compliance.operators import evaluate_operator


@pytest.mark.parametrize(
    ("operator", "current", "expected"),
    [
        ("EQ", 2, 2),
        ("NE", 2, 3),
        ("LT", 2, 3),
        ("LTE", 2, 2),
        ("GT", 3, 2),
        ("GTE", 3, 3),
        ("EXISTS", "x", True),
        ("NOT_EXISTS", None, True),
        ("IN", "a", ["a"]),
        ("NOT_IN", "b", ["a"]),
        ("COUNT_EQ", [1], 1),
        ("COUNT_LTE", [1], 2),
        ("COUNT_GTE", [1, 2], 2),
        ("MATCH_REGEX", "abc", "^a"),
        ("NOT_MATCH_REGEX", "abc", "^z"),
        ("CONTAINS", "abc", "b"),
        ("NOT_CONTAINS", "abc", "z"),
    ],
)
def test_operator_registry(operator: str, current: object, expected: object) -> None:
    assert evaluate_operator(operator, current, expected)
