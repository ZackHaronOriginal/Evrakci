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


def test_junk_required_value_is_never_silent():
    name, checks = build_name(
        "{firma}_{tarih}", {"firma": ok("***"), "tarih": ok("2024")}, {"firma"}
    )
    assert name is None and checks == ["zorunlu değer dosya adına uygun değil: firma"]
    name, checks = build_name("{a}_{b}", {"a": ok(".."), "b": ok("x")}, set())
    assert name == "x" and checks == ["dosya adına uygun değil: a"]


def test_unique_names_never_duplicates():
    names = unique_names(["a", "a", "a (2)", "A (2)"])
    assert len({n.casefold() for n in names}) == 4


def test_unique_names_turkish_i():
    names = unique_names(["KAYIŞ", "Kayış", "ışık", "IŞIK", "İz", "iz"])
    keys = [n.upper().casefold() for n in names]
    assert len(set(keys)) == 6


def test_cut_dropping_required_value():
    long = "x" * 119
    name, checks = build_name("{a}_{b}", {"a": ok(long), "b": ok("ÖNEMLİ")}, {"b"})
    assert name is None and checks == ["zorunlu değer dosya adına sığmadı: b"]


def test_more_reserved_names():
    for reserved in ("CONIN$", "conout$", "COM¹", "lpt³"):
        assert safe_filename(reserved).endswith("_")


def test_fit_names_to_path_limit(tmp_path):
    from evrakci.pipeline.naming import fit_names

    # A folder whose full path is about 180 characters, whatever the temp folder is.
    folder = tmp_path / ("ç" * max(1, 180 - len(str(tmp_path.resolve())) - 1))
    names = fit_names(["Ş" * 120, "kısa"], folder)
    budget = 250 - len(str(folder.resolve())) - len(" (99).pdf.gecici") - 1
    assert all(len(n) <= budget for n in names) and names[1] == "kısa"
    import pytest

    with pytest.raises(ValueError):
        fit_names(["a"], tmp_path / ("y" * 260))
