"""Short Kontrol performance run that fails on wrong or stale pictures, never on timing.

CI machines differ too much in speed for a time limit; the timing thresholds stay in
.claude/skills/perf-profile/perf_kontrol.py and are checked by hand (see docs/ui-goal/ci-gates.md).
What must hold on every machine is correctness: after scrolling settles every page shows its own
scan, and no frame paints a picture of another page or an outdated one.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "perf-profile"
SCRIPT = SKILL_DIR / "perf_kontrol.py"


def test_kontrol_scroll_shows_the_right_pictures_at_300_pages(tmp_path):
    out, log = tmp_path / "out.json", tmp_path / "frames.jsonl"
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--pages", "300", "--runs", "1",
         "--frame-log", str(log), "--out", str(out)],
        env=env, capture_output=True, text=True, timeout=600)
    # exit 1 only means a timing threshold was missed, which is not judged here
    assert done.returncode in (0, 1), done.stdout + done.stderr
    data = json.loads(out.read_text())
    median = data.get("median", data)  # one run is written as it is, several as statistics
    assert median["settled_loaded_pct_real"] == 100, median
    assert median["frames_with_wrong"] == 0, median
    assert median["frames_with_stale"] == 0, median
