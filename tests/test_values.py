"""value_level: the one rule for a value's Güven level (window and CLI agree)."""

from evrakci.pipeline.templates.values import EMIN_AT, SectionReading, VariableValue, value_level


def test_an_unread_value_is_okunmadi():
    assert value_level(None) == "okunmadi"


def test_an_unflagged_value_is_emin_from_090_else_orta():
    assert EMIN_AT == 0.90
    assert value_level(VariableValue("x", 0.90, 0, False)) == "emin"
    assert value_level(VariableValue("x", 0.8999, 0, False)) == "orta"
    assert value_level(VariableValue("x", 0.5, 0, False, edited=True)) == "emin"


def test_a_flagged_value_with_a_reading_or_suggestion_is_kontrol():
    assert value_level(VariableValue("482I3", 0.5, 0, True)) == "kontrol"
    assert value_level(VariableValue("", 0.0, None, True, "77")) == "kontrol"
    only_reading = VariableValue("", 0.0, None, True, "", (SectionReading(0, "4", 0.4),))
    assert value_level(only_reading) == "kontrol"


def test_a_flagged_value_with_nothing_read_is_okunamadi():
    assert value_level(VariableValue("", 0.0, None, True)) == "okunamadi"
    empty = VariableValue("", 0.0, None, True, "", (SectionReading(0, "", 0.0),))
    assert value_level(empty) == "okunamadi"
