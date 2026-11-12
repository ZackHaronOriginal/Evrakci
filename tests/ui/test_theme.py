from evrakci.ui import theme


def _contrast(a: str, b: str) -> float:
    def lum(hex_colour: str) -> float:
        channels = [int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_tokens_match_design_record():
    t = theme.TOKENS
    assert t["shell"] == "#3f5a4c"
    assert t["rider"] == "#e8731a"
    assert {"qr", "filter", "manual", "manila", "index_red", "card", "ink"} <= set(t)


def test_text_pairs_meet_wcag_aa():
    t = theme.TOKENS
    for fg, bg in [("ink", "card"), ("ink_2", "card"), ("on_shell", "shell"),
                   ("on_shell_2", "shell"), ("check_ink", "check_wash"), ("manila_ink", "manila"),
                   ("ink_2", "key_cap"), ("ink", "hover"), ("ink", "row_cur"),
                   ("on_shell", "shell_3"), ("paper", "ink")]:
        assert _contrast(t[fg], t[bg]) >= 4.5, (fg, bg)


def test_stylesheet_uses_tokens_and_system_font():
    css = theme.stylesheet()
    assert theme.TOKENS["shell"] in css
    assert "Segoe UI" in css
    assert "#ff00ff" not in css
