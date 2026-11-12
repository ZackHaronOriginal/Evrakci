"""OCR model files: where they live, where they come from, and checksum checks.

Model files are never trusted unless their SHA-256 matches the one RapidOCR
publishes for that model.
"""

from __future__ import annotations

import hashlib
import http.client
import os
import sys
import urllib.request
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import platformdirs

from evrakci.pipeline.ocr.engine import EngineUnavailable


@dataclass(frozen=True)
class ModelFile:
    key: str
    url: str
    sha256: str
    file_name: str


def app_dir() -> Path | None:
    """The installed app's own folder (where bundled tools live), or None when not frozen."""
    configured = os.environ.get("EVRAKCI_UYGULAMA_KLASORU")
    if configured:
        return Path(configured)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return None


def data_dir() -> Path:
    return platformdirs.user_data_path("Evrakci", appauthor=False)


def model_dir() -> Path:
    configured = os.environ.get("EVRAKCI_MODEL_DIR")
    return Path(configured) if configured else data_dir() / "models"


def official_model(version: str, kind: str, key: str) -> ModelFile:
    """The model's official URL and checksum, from the installed rapidocr package."""
    import yaml  # installed with rapidocr

    text = resources.files("rapidocr").joinpath("default_models.yaml").read_text("utf-8")
    entry = yaml.safe_load(text)["onnxruntime"][version][kind][key]
    return ModelFile(key, entry["model_dir"], entry["SHA256"].lower(), f"{key}.onnx")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_model(model: ModelFile, download: bool = True) -> Path:
    """A verified local copy of the model, downloading it if allowed."""
    path = model_dir() / model.file_name
    if path.is_file():
        if _sha256(path) == model.sha256:
            return path
        path.unlink()
        if not download:
            raise EngineUnavailable(f"Model dosyası doğrulanamadı ve silindi: {model.file_name}")
    elif not download:
        raise EngineUnavailable(f"Model dosyası yok: {model.file_name}")

    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".part")
    try:
        with urllib.request.urlopen(model.url, timeout=60) as response, open(partial, "wb") as out:
            for chunk in iter(lambda: response.read(1 << 20), b""):
                out.write(chunk)
    except (OSError, http.client.HTTPException) as error:  # a cut-off transfer is the latter
        partial.unlink(missing_ok=True)
        raise EngineUnavailable(f"Model indirilemedi: {model.file_name} ({error!r})") from error
    if _sha256(partial) != model.sha256:
        partial.unlink(missing_ok=True)
        raise EngineUnavailable(f"İndirilen model doğrulanamadı: {model.file_name}")
    os.replace(partial, path)
    return path
