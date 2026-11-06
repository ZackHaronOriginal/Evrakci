"""Scoring OCR readings. Exact code points: Turkish case is never folded."""

from __future__ import annotations

import unicodedata

TURKISH_CHARS = "ıiİIşŞğĞçÇöÖüÜ"

Op = tuple[str, str | None, str | None]


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


def edit_ops(truth: str, read: str) -> list[Op]:
    """Levenshtein alignment: ("eq" | "sub" | "del" | "ins", truth char, read char)."""
    rows, cols = len(truth) + 1, len(read) + 1
    cost = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        cost[i][0] = i
    for j in range(cols):
        cost[0][j] = j
    for i in range(1, rows):
        for j in range(1, cols):
            same = truth[i - 1] == read[j - 1]
            cost[i][j] = min(
                cost[i - 1][j - 1] + (0 if same else 1),
                cost[i - 1][j] + 1,
                cost[i][j - 1] + 1,
            )
    ops: list[Op] = []
    i, j = len(truth), len(read)
    while i or j:
        if i and j and cost[i][j] == cost[i - 1][j - 1] + (truth[i - 1] != read[j - 1]):
            kind = "eq" if truth[i - 1] == read[j - 1] else "sub"
            ops.append((kind, truth[i - 1], read[j - 1]))
            i, j = i - 1, j - 1
        elif i and cost[i][j] == cost[i - 1][j] + 1:
            ops.append(("del", truth[i - 1], None))
            i -= 1
        else:
            ops.append(("ins", None, read[j - 1]))
            j -= 1
    ops.reverse()
    return ops


def cer(truth: str, read: str) -> float:
    truth, read = normalize(truth), normalize(read)
    edits = sum(1 for kind, _, _ in edit_ops(truth, read) if kind != "eq")
    return edits / max(len(truth), 1) if truth or read else 0.0


def turkish_char_errors(truth: str, read: str) -> tuple[int, int]:
    """(wrong, total) over truth characters that are Turkish-sensitive."""
    wrong = total = 0
    for kind, truth_char, _ in edit_ops(normalize(truth), normalize(read)):
        if truth_char is not None and truth_char in TURKISH_CHARS:
            total += 1
            wrong += kind != "eq"
    return wrong, total


def exact(truth: str, read: str) -> bool:
    return normalize(truth) == normalize(read)


def box_hit(truth_box: tuple[int, int, int, int], read_box: tuple[int, int, int, int]) -> bool:
    cx = (read_box[0] + read_box[2]) / 2
    cy = (read_box[1] + read_box[3]) / 2
    return truth_box[0] <= cx <= truth_box[2] and truth_box[1] <= cy <= truth_box[3]
