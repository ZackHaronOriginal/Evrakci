"""Run several OCR engines on the same pages and write a Turkish report."""

from __future__ import annotations

import importlib.util
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from evrakci.pipeline.ocr.engine import EngineUnavailable, OcrEngine
from evrakci.pipeline.ocr.metrics import box_hit, cer, exact, turkish_char_errors
from evrakci.pipeline.ocr.models import model_dir
from evrakci.pipeline.ocr.preprocess import prepare_page, prepare_region
from evrakci.pipeline.ocr.synthetic import SyntheticPage
from evrakci.pipeline.ocr.tesseract import find_tesseract, system_tessdata, tessdata_dir

_SAMPLE_LIMIT = 15


@dataclass
class EngineResult:
    name: str
    unavailable: str | None = None
    fields: int = 0
    exact: int = 0
    cer: float = 0.0
    tr_wrong: int = 0
    tr_total: int = 0
    page_seconds: float = 0.0
    aligned: int = 0
    words: int = 0
    samples: list[tuple[str, str]] = field(default_factory=list)


def compare_synthetic(
    engines: Sequence[OcrEngine], pages: Sequence[SyntheticPage], preprocess: bool = False
) -> list[EngineResult]:
    """Score each engine on the same pages. `preprocess` cleans every crop and page first."""
    results = []
    for engine in engines:
        result = EngineResult(engine.name, unavailable=engine.available())
        if result.unavailable is None:
            try:
                _score(engine, pages, result, preprocess)
            except EngineUnavailable as error:
                result = EngineResult(engine.name, unavailable=str(error))
        results.append(result)
    return results


def _score(
    engine: OcrEngine, pages: Sequence[SyntheticPage], result: EngineResult, preprocess: bool
) -> None:
    error_sum = 0.0
    seconds = 0.0
    for page in pages:
        for truth in page.fields:
            crop = page.image.crop(truth.box)
            reading = engine.read_region(prepare_region(crop) if preprocess else crop)
            result.fields += 1
            if exact(truth.text, reading.text):
                result.exact += 1
            elif len(result.samples) < _SAMPLE_LIMIT:
                result.samples.append((truth.text, reading.text))
            error_sum += cer(truth.text, reading.text)
            wrong, total = turkish_char_errors(truth.text, reading.text)
            result.tr_wrong += wrong
            result.tr_total += total
        image = prepare_page(page.image) if preprocess else page.image
        started = time.perf_counter()
        words = engine.read_page(image)
        seconds += time.perf_counter() - started
        result.words += len(page.words)
        result.aligned += sum(
            any(box_hit(truth.box, word.box) for word in words) for truth in page.words
        )
    result.cer = error_sum / max(result.fields, 1)
    result.page_seconds = seconds / max(len(pages), 1)


def _tree_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if not path.is_dir():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def _package_dir(module: str) -> Path | None:
    spec = importlib.util.find_spec(module)
    if spec is None or not spec.submodule_search_locations:
        return None
    return Path(next(iter(spec.submodule_search_locations)))


def install_sizes() -> dict[str, int]:
    """Rough install size per engine, in bytes. Engines that aren't installed are left out."""
    sizes: dict[str, int] = {}
    binary = find_tesseract()
    tessdata = system_tessdata()
    if binary is not None:
        base = (
            _tree_size(binary.parent)
            if binary.parent.name == "Tesseract-OCR"
            else _tree_size(binary)
        )
        if tessdata is not None:
            sizes["tesseract-tur (sistem)"] = base + _tree_size(tessdata / "tur.traineddata")
        for variant in ("fast", "standard", "best"):
            data = tessdata_dir(variant) / "tur.traineddata"
            if data.is_file():
                sizes[f"tesseract-tur_{variant}"] = base + _tree_size(data)
    runtime = [_package_dir(m) for m in ("onnxruntime", "rapidocr", "cv2")]
    if all(runtime):
        base = sum(_tree_size(path) for path in runtime if path)
        det = _tree_size(model_dir() / "ch_PP-OCRv5_det_mobile.onnx")
        for name, key in (
            ("rapidocr-v5-latin", "latin_PP-OCRv5_rec_mobile"),
            ("rapidocr-v6-multi", "multi_PP-OCRv6_rec_small"),
        ):
            rec = model_dir() / f"{key}.onnx"
            if rec.is_file():
                sizes[name] = base + det + _tree_size(rec)
    return sizes


def cell(text: str) -> str:
    """Text safe inside a Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ")


def _percent(part: float, whole: float) -> str:
    return f"{100 * part / whole:.1f}" if whole else "-"


def render_report(
    results: Sequence[EngineResult], sizes: dict[str, int], title: str, notes: Sequence[str]
) -> str:
    lines = [f"# {title}", ""]
    lines += [
        "| Motor | Tam doğru % | Karakter hatası % | Türkçe harf hatası % "
        "| Saniye/sayfa | Metin katmanı hizası % | Kurulum MB |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        size = f"{sizes[r.name] / 1024 / 1024:.1f}" if r.name in sizes else "-"
        if r.unavailable:
            lines.append(f"| {r.name} | kullanılamıyor: {cell(r.unavailable)} | | | | | {size} |")
            continue
        lines.append(
            f"| {r.name} | {_percent(r.exact, r.fields)} | {100 * r.cer:.1f} "
            f"| {_percent(r.tr_wrong, r.tr_total)} | {r.page_seconds:.2f} "
            f"| {_percent(r.aligned, r.words)} | {size} |"
        )
    fields = max((r.fields for r in results), default=0)
    lines += ["", f"Alan sayısı: {fields}.", ""]
    for r in results:
        if r.unavailable or not r.samples:
            continue
        lines += [f"## Hatalı okumalar: {r.name}", "", "| Doğrusu | Okunan |", "|---|---|"]
        lines += [f"| {cell(truth)} | {cell(read) or '(boş)'} |" for truth, read in r.samples]
        lines.append("")
    if notes:
        lines += ["## Notlar", ""] + [f"- {note}" for note in notes] + [""]
    return "\n".join(lines)
