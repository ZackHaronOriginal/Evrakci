from evrakci.pipeline.naming import build_name, safe_filename, unique_names
from evrakci.pipeline.templates.read import VariableValue


def ok(text):
    return VariableValue(text, 0.9, 0, False)


def unsure(suggestion=""):
    return VariableValue("", 0.0, None, True, suggestion)


def test_windows_forbidden_and_reserved():
    assert safe_filename('A/B:C*?"<>|D') == "ABCD"
    assert safe_filename("CON") == "CON_" and safe_filename("nul") == "nul_"
    assert safe_filename("com1") == "com1_" and safe_filename("Console") == "Console"
    assert safe_filename("Örnek Ltd. Şti. ") == "Örnek Ltd. Şti"
    assert safe_filename("a\tb\n  c") == "a b c" and safe_filename("...") == ""


def test_turkish_kept_and_nfc():
    assert safe_filename("İSTANBUL Çağrı ığdır") == "İSTANBUL Çağrı ığdır"
    assert safe_filename("İstanbul") == safe_filename("İstanbul")


def test_long_name_cut():
    assert len(safe_filename("Ş" * 300)) == 120


def test_required_missing_gives_none():
    name, checks = build_name("{A}_{B}", {"A": ok("x"), "B": unsure("y")}, {"B"})
    assert name is None and checks == ["zorunlu değer eksik: B"]
    name, checks = build_name("{A}_{B}", {"A": ok("x")}, {"B"})
    assert name is None and checks == ["zorunlu değer eksik: B"]


def test_flagged_optional_left_out_and_separators_collapsed():
    values = {"A": ok("a"), "B": unsure(), "C": ok("c")}
    assert build_name("{A}_{B}_{C}", values, set()) == ("a_c", ["okunamadı: B"])
    assert build_name("{B} - {A}", values, set()) == ("a", ["okunamadı: B"])
    assert build_name("{B}", values, set()) == ("", ["okunamadı: B"])


def test_values_made_safe_inside_pattern():
    name, _ = build_name("{A}_{B}", {"A": ok("12/34"), "B": ok("Örnek: Şti")}, set())
    assert name == "1234_Örnek Şti"


def test_unique_names_case_insensitive():
    assert unique_names(["Örnek", "örnek", "Örnek", "Başka"]) == [
        "Örnek",
        "örnek (2)",
        "Örnek (3)",
        "Başka",
    ]
