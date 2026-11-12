import pytest
from PySide6.QtCore import QObject, QPointF, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from evrakci.ui import motion
from evrakci.ui.motion import Duration


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def _reset():
    yield
    motion.set_reduced_motion_override(None)


def test_tokens_values_and_cap():
    assert [int(d) for d in Duration] == [0, 80, 120, 180, 240]
    assert max(Duration) <= 240 == motion.MAX_DURATION


def test_duration_normal_and_reduced(app):
    motion.set_reduced_motion_override(False)
    assert [motion.duration(d) for d in Duration] == [0, 80, 120, 180, 240]
    motion.set_reduced_motion_override(True)
    assert all(motion.duration(d) == 0 for d in Duration)


def test_unknown_duration_rejected():
    with pytest.raises(ValueError):
        motion.duration(300)


def test_override_wins_over_system(app):
    motion.set_reduced_motion_override(True)
    assert motion.reduced_motion() is True
    motion.set_reduced_motion_override(False)
    assert motion.reduced_motion() is False
    motion.set_reduced_motion_override(None)
    assert motion.reduced_motion() == motion.system_reduced_motion()


@pytest.mark.parametrize(
    ("curve", "points"),
    [
        (motion.standard, (0.2, 0, 0, 1)),
        (motion.enter, (0, 0, 0, 1)),
        (motion.exit_, (0.3, 0, 1, 1)),
    ],
)
def test_curve_control_points(curve, points):
    spline = curve().toCubicSpline()
    assert spline[:2] == [QPointF(points[0], points[1]), QPointF(points[2], points[3])]
    assert spline[2] == QPointF(1, 1)


def test_linear_curve():
    assert motion.linear().valueForProgress(0.25) == pytest.approx(0.25)


def test_animate_reduced_sets_end_value(app):
    motion.set_reduced_motion_override(True)
    obj = QObject()
    obj.setProperty("x", 0.0)
    assert motion.animate(obj, b"x", 0.0, 5.0, Duration.SLOW) is None
    assert obj.property("x") == 5.0


def test_animate_flag_off_is_instant(app):
    motion.set_reduced_motion_override(False)
    obj = QObject()
    assert motion.animate(obj, b"x", 0.0, 3.0, Duration.SLOW, animate=False) is None
    assert obj.property("x") == 3.0


def test_animate_runs_when_allowed(app):
    motion.set_reduced_motion_override(False)
    widget = QWidget()
    anim = motion.animate(widget, b"windowOpacity", 0.0, 1.0, Duration.FAST)
    assert anim is not None and anim.duration() == 80


def test_fade_helpers_reduced(app):
    motion.set_reduced_motion_override(True)
    w = QWidget()
    assert motion.fade_in(w) is None
    assert w.isVisible() and w.graphicsEffect().opacity() == 1.0
    assert motion.fade_out(w) is None
    assert not w.isVisible()


def test_busy_cursor_not_shown_for_short_block(app):
    with motion.busy_cursor():
        pass
    assert QApplication.overrideCursor() is None


def test_busy_cursor_shown_after_delay_and_restored(app):
    with motion.busy_cursor(delay_ms=20):
        loop_done = []
        QTimer.singleShot(80, lambda: loop_done.append(1))
        while not loop_done:
            app.processEvents()
        assert QApplication.overrideCursor() is not None
    assert QApplication.overrideCursor() is None
