import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "perf-profile"
SCRIPT = SKILL_DIR / "perf_kontrol.py"
NEW_METRICS = [
    "first_paint_ms", "renders_at_first_paint", "renders_at_first_settle", "frame_p50_ms",
    "frame_p95_ms", "frame_max_ms", "settle_ms", "settled_loaded_pct", "rss_mb_after_sweep",
    "cache_size", "frames_with_wrong", "frames_with_stale", "blank_rows_after_settle",
    "max_blank_rows_in_frame",
]


def test_perf_script_writes_runs_statistics_and_a_frame_log(tmp_path):
    out, log = tmp_path / "out.json", tmp_path / "frames.jsonl"
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--pages", "60", "--steps", "5", "--runs", "2",
         "--frame-log", str(log), "--out", str(out)],
        env=env, capture_output=True, text=True, timeout=120)
    assert done.returncode in (0, 1), done.stdout + done.stderr  # 1 = a threshold was missed
    data = json.loads(out.read_text())
    assert len(data["runs"]) == 2
    for section in ("median", "min", "max", "spread_pct"):
        for key in NEW_METRICS:
            value = data[section][key]
            assert isinstance(value, (int, float)) and not isinstance(value, bool), (section, key)
    assert data["median"]["backing_store_blit_verified"] == 1
    lines = [json.loads(line) for line in log.read_text().splitlines()]
    assert lines and {"step", "scroll", "counts", "examples"} <= set(lines[0])
    assert set(lines[0]["counts"]) == {"ok", "blank", "wrong", "stale"}
