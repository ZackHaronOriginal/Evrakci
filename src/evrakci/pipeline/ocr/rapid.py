"""RapidOCR: Baidu's PaddleOCR models on ONNX Runtime (optional extra `rapidocr`)."""

from __future__ import annotations

import logging

from PIL import Image

from evrakci.pipeline.ocr.engine import EngineUnavailable, Reading, Word, nfc
from evrakci.pipeline.ocr.models import ensure_model, official_model

_DET = ("PP-OCRv5", "det", "ch_PP-OCRv5_det_mobile")
# The text detector misses text near the image edge, so every image gets a white border.
_REGION_PADDING = 48


def _reading_order(
    lines: list[tuple[str, tuple[int, int, int, int], float]],
) -> list[tuple[str, tuple[int, int, int, int], float]]:
    """Top to bottom, then left to right. Boxes whose vertical centres are close share a line."""
    rows: list[list[tuple[str, tuple[int, int, int, int], float]]] = []
    for line in sorted(lines, key=lambda item: (item[1][1] + item[1][3]) / 2):
        _, (_, y0, _, y1), _ = line
        centre, height = (y0 + y1) / 2, y1 - y0
        if rows:
            _, (_, ry0, _, ry1), _ = rows[-1][0]
            if abs(centre - (ry0 + ry1) / 2) <= max(height, ry1 - ry0) / 2:
                rows[-1].append(line)
                continue
        rows.append([line])
    return [line for row in rows for line in sorted(row, key=lambda item: item[1][0])]


def _line_to_words(text: str, box: tuple[int, int, int, int], score: float) -> list[Word]:
    """Split a detected line into words, sharing its width by character count."""
    parts = text.split()
    if not parts:
        return []
    x0, y0, x1, y1 = box
    total = sum(len(p) for p in parts) + len(parts) - 1
    per_char = (x1 - x0) / max(total, 1)
    words, cursor = [], 0
    for part in parts:
        start = x0 + round(cursor * per_char)
        end = x0 + round((cursor + len(part)) * per_char)
        words.append(Word(nfc(part), (start, y0, end, y1), score))
        cursor += len(part) + 1
    return words


class RapidOcrEngine:
    def __init__(
        self,
        rec_key: str = "latin_PP-OCRv5_rec_mobile",
        rec_version: str = "PP-OCRv5",
        name: str = "rapidocr-v5-latin",
        download: bool = True,
    ) -> None:
        self.rec_key = rec_key
        self.rec_version = rec_version
        self.name = name
        self.download = download
        self._engine = None
        self._reason: str | None = None
        self._checked = False

    def available(self) -> str | None:
        if not self._checked:
            self._checked = True
            try:
                self._build()
            except EngineUnavailable as error:
                self._reason = str(error)
        return self._reason

    def _build(self) -> None:
        try:
            from rapidocr import LangRec, ModelType, OCRVersion, RapidOCR
        except ImportError as error:
            raise EngineUnavailable(
                'RapidOCR kurulu değil (pip install "evrakci[rapidocr]")'
            ) from error
        try:
            det = ensure_model(official_model(*_DET), download=self.download)
            rec = ensure_model(
                official_model(self.rec_version, "rec", self.rec_key), download=self.download
            )
        except KeyError as error:
            raise EngineUnavailable(f"Bu RapidOCR sürümünde model yok: {error}") from error
        params = {
            "Global.use_cls": False,
            "Det.model_path": str(det),
            "Det.ocr_version": OCRVersion(_DET[0]),
            "Rec.model_path": str(rec),
            "Rec.ocr_version": OCRVersion(self.rec_version),
        }
        lang = self.rec_key.split("_")[0]
        if lang in {item.value for item in LangRec}:
            params["Rec.lang_type"] = LangRec(lang)
        model_type = self.rec_key.rsplit("_", 1)[-1]
        if model_type in {item.value for item in ModelType}:
            params["Rec.model_type"] = ModelType(model_type)
        # RapidOCR logs every model load and every empty crop; keep the CLI output clean.
        logging.getLogger("RapidOCR").setLevel(logging.ERROR)
        try:
            self._engine = RapidOCR(params=params)
            logging.getLogger("RapidOCR").setLevel(logging.ERROR)
        except Exception as error:  # RapidOCR raises plain exceptions on bad setups
            raise EngineUnavailable(f"RapidOCR başlatılamadı: {error}") from error

    def _lines(self, image: Image.Image) -> list[tuple[str, tuple[int, int, int, int], float]]:
        reason = self.available()
        if reason:
            raise EngineUnavailable(reason)
        import numpy as np

        pad = _REGION_PADDING
        padded = Image.new("RGB", (image.width + 2 * pad, image.height + 2 * pad), "white")
        padded.paste(image.convert("RGB"), (pad, pad))
        result = self._engine(np.asarray(padded))
        if result.boxes is None or result.txts is None:
            return []
        lines = []
        for points, text, score in zip(result.boxes, result.txts, result.scores, strict=True):
            xs = [int(p[0]) - pad for p in points]
            ys = [int(p[1]) - pad for p in points]
            lines.append((text, (min(xs), min(ys), max(xs), max(ys)), float(score)))
        return _reading_order(lines)

    def read_page(self, image: Image.Image) -> list[Word]:
        words: list[Word] = []
        for text, box, score in self._lines(image):
            words.extend(_line_to_words(text, box, score))
        return words

    def read_region(self, image: Image.Image) -> Reading:
        lines = self._lines(image)
        if not lines:
            return Reading("", 0.0)
        text = nfc(" ".join(text for text, _, _ in lines))
        return Reading(text, sum(score for _, _, score in lines) / len(lines))
