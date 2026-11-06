"""The usual clean-up before OCR: straighten and turn black-and-white.

Applied the same way to every engine when a comparison asks for it.
"""

from __future__ import annotations

from PIL import Image

# Search range and step for skew, in degrees.
_MAX_SKEW = 5.0
_STEP = 0.1
_WORK_WIDTH = 800  # estimate on a smaller copy, for speed
# Below this angle a crop is left as it is.
_MIN_CORRECTION = 0.2


def binarize(image: Image.Image) -> Image.Image:
    """Black and white with Otsu's threshold."""
    gray = image.convert("L")
    histogram = gray.histogram()
    total = sum(histogram)
    weighted_total = sum(i * count for i, count in enumerate(histogram))
    best_threshold, best_variance = 128, -1.0
    background = weighted_background = 0.0
    for threshold, count in enumerate(histogram):
        background += count
        if background == 0:
            continue
        foreground = total - background
        if foreground == 0:
            break
        weighted_background += threshold * count
        mean_background = weighted_background / background
        mean_foreground = (weighted_total - weighted_background) / foreground
        variance = background * foreground * (mean_background - mean_foreground) ** 2
        if variance > best_variance:
            best_variance, best_threshold = variance, threshold
    return gray.point(lambda v: 255 if v > best_threshold else 0)


def _row_score(image: Image.Image) -> float:
    """How sharply ink is concentrated in rows: high when text lines are horizontal."""
    width, height = image.size
    data = image.tobytes()
    rows = [width - sum(data[y * width : (y + 1) * width]) / 255 for y in range(height)]
    return sum((rows[i + 1] - rows[i]) ** 2 for i in range(len(rows) - 1))


def estimate_skew(image: Image.Image) -> float:
    """The angle (degrees, counter-clockwise) the content is rotated by."""
    small = binarize(image)
    if small.width > _WORK_WIDTH:
        small = small.resize(
            (_WORK_WIDTH, max(1, round(small.height * _WORK_WIDTH / small.width)))
        ).point(lambda v: 255 if v > 128 else 0)
    best_angle, best_score = 0.0, -1.0
    steps = round(_MAX_SKEW / _STEP)
    for step in range(-steps, steps + 1):
        angle = step * _STEP
        straightened = small.rotate(-angle, fillcolor=255)
        score = _row_score(straightened)
        if score > best_score:
            best_score, best_angle = score, angle
    return best_angle


def prepare_region(image: Image.Image) -> Image.Image:
    """Straighten a crop if it is visibly skewed, then make it black and white."""
    angle = estimate_skew(image)
    if abs(angle) >= _MIN_CORRECTION:
        image = image.convert("L").rotate(-angle, resample=Image.Resampling.BICUBIC, fillcolor=255)
    return binarize(image)


def prepare_page(image: Image.Image) -> Image.Image:
    """Black and white only, so word positions stay where they were on the page."""
    return binarize(image)
