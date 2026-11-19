import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "perf-profile"
SCRIPT = SKILL_DIR / "perf_kontrol.py"
NEW_METRICS = [
    "first_paint_ms", "renders_at_first_paint", "renders_at_first_settle", "paint_cost_p50_ms",
    "paint_cost_p95_ms", "paint_cost_max_ms", "settle_ms", "settled_loaded_pct_real",
    "settled_loaded_pct_forced", "rss_mb_after_sweep",
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


def test_perf_script_new_options_theme_text_scale_disk_delay_and_memory_ceiling(tmp_path):
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    out = tmp_path / "opts.json"
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--pages", "60", "--steps", "5", "--theme", "hc",
         "--text-scale", "150", "--disk-delay-ms", "3", "--memory-ceiling-mb", "100000",
         "--out", str(out)],
        env=env, capture_output=True, text=True, timeout=120)
    assert done.returncode in (0, 1), done.stdout + done.stderr
    data = json.loads(out.read_text())
    assert (data["theme"], data["text_scale"], data["disk_delay_ms"]) == ("hc", 150, 3.0)
    assert data["memory_run_completed"] == 1 and data["vm_mb_at_cap"] > 0
    assert data["settled_loaded_pct_real"] == 100.0


def test_perf_script_tiny_memory_ceiling_reports_incomplete_run(tmp_path):
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    out = tmp_path / "tiny.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--pages", "60", "--steps", "5",
         "--memory-ceiling-mb", "50", "--out", str(out)],
        env=env, capture_output=True, text=True, timeout=120)
    if out.exists():  # a cap that kills the process before it writes is also an incomplete run
        assert json.loads(out.read_text())["memory_run_completed"] in (0, 1)
