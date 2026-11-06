"""App settings, stored as UTF-8 JSON in the app data folder."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from evrakci.pipeline.ocr.models import data_dir

KEEP = "sakla"
DELETE_AFTER_EXPORT = "disa-aktarinca-sil"


class SettingsError(ValueError):
    """A bad setting value. The message is shown to staff (Turkish)."""


@dataclass(frozen=True)
class Settings:
    # "sakla" (never delete), "disa-aktarinca-sil" (after a full export), or a number of days.
    retention: str = KEEP

    def __post_init__(self) -> None:
        value = self.retention
        if value in (KEEP, DELETE_AFTER_EXPORT):
            return
        if not (value.isdigit() and int(value) > 0):
            raise SettingsError(
                f"Geçersiz saklama ayarı: {value!r} (sakla, disa-aktarinca-sil veya gün sayısı)"
            )

    @property
    def retention_days(self) -> int | None:
        return int(self.retention) if self.retention.isdigit() else None


def settings_path() -> Path:
    configured = os.environ.get("EVRAKCI_AYARLAR")
    return Path(configured) if configured else data_dir() / "settings.json"


def load_settings(path: Path | None = None) -> Settings:
    path = Path(path) if path else settings_path()
    if not path.is_file():
        return Settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return Settings(str(data.get("saklama", KEEP)))
    except (OSError, ValueError) as error:
        raise SettingsError(f"Ayar dosyası okunamadı: {path} ({error})") from error


def save_settings(settings: Settings, path: Path | None = None) -> None:
    path = Path(path) if path else settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps({"saklama": settings.retention}, ensure_ascii=False), encoding="utf-8"
    )
    os.replace(temporary, path)
