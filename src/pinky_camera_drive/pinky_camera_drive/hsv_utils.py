"""Pure helpers for yellow HSV calibration and runtime S/V adaptation.

OpenCV HSV scale: H 0..179, S 0..255, V 0..255. No ROS imports here so the
math is unit-testable without a camera.
"""

import datetime
import os
import re
import shutil
import tempfile

import numpy as np
import yaml

HSV_KEYS = (
    'yellow_h_low', 'yellow_h_high',
    'yellow_s_low', 'yellow_s_high',
    'yellow_v_low', 'yellow_v_high',
)

# A click/pixel only counts as yellow when its hue is inside this band and it
# has some colour at all (grey/white/black pixels have meaningless hue).
H_GUARD = (15, 45)
MIN_SAMPLE_S = 40
MIN_SAMPLE_V = 40

# Lighting mostly moves S/V, so they get wider percentiles and margins than H.
H_PERCENTILES = (5.0, 95.0)
H_MARGIN = 3
S_PERCENTILES = (2.0, 98.0)
S_MARGIN = 20
V_PERCENTILES = (2.0, 98.0)
V_MARGIN = 25
# Floors keep a calibration from accepting near-grey or near-black pixels.
S_LOW_FLOOR = 50
V_LOW_FLOOR = 40
MIN_H_WIDTH = 4

# Runtime adaptation gains (offset per unit of scene-V change), before the
# hard clamps from YAML. ponytail: fixed gains; promote to YAML if field tests
# show the line V does not track the floor V roughly 1:1.
ADAPT_V_GAIN = 1.0
ADAPT_S_GAIN = 0.5


def sample_patch(hsv, x, y, size=11):
    """Return the (N, 3) HSV pixels of a size x size patch centred on (x, y).

    Pixels outside the image are ignored; an off-image click gives N == 0.
    """
    half = max(int(size), 1) // 2
    height, width = hsv.shape[:2]
    x0, x1 = max(int(x) - half, 0), min(int(x) + half + 1, width)
    y0, y1 = max(int(y) - half, 0), min(int(y) + half + 1, height)
    if x0 >= x1 or y0 >= y1:
        return np.empty((0, 3), dtype=np.uint8)
    return hsv[y0:y1, x0:x1].reshape(-1, 3).copy()


def is_plausible_yellow(pixels):
    """Return (ok, reason) for one click patch, judged by its medians."""
    if len(pixels) == 0:
        return False, 'outside image'
    h, s, v = (float(np.median(pixels[:, i])) for i in range(3))
    if not H_GUARD[0] <= h <= H_GUARD[1]:
        return False, f'hue {h:.0f} not yellow ({H_GUARD[0]}..{H_GUARD[1]})'
    if s < MIN_SAMPLE_S:
        return False, f'saturation {s:.0f} too low (grey/white)'
    if v < MIN_SAMPLE_V:
        return False, f'value {v:.0f} too dark'
    return True, 'ok'


def _yellow_pixels(pixels):
    """Drop individual pixels outside the guard band, then H outliers (MAD)."""
    pixels = np.asarray(pixels).reshape(-1, 3)
    keep = (
        (pixels[:, 0] >= H_GUARD[0]) & (pixels[:, 0] <= H_GUARD[1])
        & (pixels[:, 1] >= MIN_SAMPLE_S) & (pixels[:, 2] >= MIN_SAMPLE_V)
    )
    pixels = pixels[keep]
    if len(pixels) == 0:
        return pixels
    hue = pixels[:, 0].astype(np.float64)
    median = np.median(hue)
    mad = np.median(np.abs(hue - median)) * 1.4826
    return pixels[np.abs(hue - median) <= max(3.0 * mad, 3.0)]


def robust_hsv_bounds(pixels):
    """Return (lower, upper) uint8 arrays from pooled yellow sample pixels.

    Percentiles + margins, never min/max or mean, so reflections and shadow
    edges in a few pixels cannot stretch the range. Raises ValueError when
    the samples cannot give a sane yellow range.
    """
    clean = _yellow_pixels(pixels)
    if len(clean) < 20:
        raise ValueError(f'only {len(clean)} usable yellow pixels')
    channels = clean.astype(np.float64)
    h_lo, h_hi = np.percentile(channels[:, 0], H_PERCENTILES)
    s_lo, s_hi = np.percentile(channels[:, 1], S_PERCENTILES)
    v_lo, v_hi = np.percentile(channels[:, 2], V_PERCENTILES)
    lower = [
        max(int(np.floor(h_lo)) - H_MARGIN, H_GUARD[0]),
        max(int(np.floor(s_lo)) - S_MARGIN, S_LOW_FLOOR),
        max(int(np.floor(v_lo)) - V_MARGIN, V_LOW_FLOOR),
    ]
    upper = [
        min(int(np.ceil(h_hi)) + H_MARGIN, H_GUARD[1]),
        min(int(np.ceil(s_hi)) + S_MARGIN, 255),
        min(int(np.ceil(v_hi)) + V_MARGIN, 255),
    ]
    lower, upper = np.array(lower), np.array(upper)
    validate_bounds(lower, upper)
    return lower.astype(np.uint8), upper.astype(np.uint8)


def validate_bounds(lower, upper):
    """Raise ValueError unless lower/upper form a sane yellow HSV range."""
    lower = [int(v) for v in lower]
    upper = [int(v) for v in upper]
    if len(lower) != 3 or len(upper) != 3:
        raise ValueError('HSV bounds must have 3 channels')
    if not (0 <= lower[0] <= upper[0] <= 179):
        raise ValueError(f'H range {lower[0]}..{upper[0]} invalid')
    if not (H_GUARD[0] <= lower[0] and upper[0] <= H_GUARD[1]):
        raise ValueError(f'H range {lower[0]}..{upper[0]} outside yellow guard')
    if upper[0] - lower[0] < MIN_H_WIDTH:
        raise ValueError(f'H range {lower[0]}..{upper[0]} too narrow')
    for name, lo, hi in (('S', lower[1], upper[1]), ('V', lower[2], upper[2])):
        if not (0 <= lo < hi <= 255):
            raise ValueError(f'{name} range {lo}..{hi} invalid')


def in_range_fraction(pixels, lower, upper):
    """Fraction of (N, 3) pixels inside [lower, upper] (0.0 when empty)."""
    pixels = np.asarray(pixels).reshape(-1, 3)
    if len(pixels) == 0:
        return 0.0
    inside = np.all((pixels >= lower) & (pixels <= upper), axis=1)
    return float(np.mean(inside))


# ---------------------------------------------------------------- runtime --

def scene_brightness(frame_bgr, y_ratio):
    """Median V (= max of B, G, R) of the image rows below y_ratio.

    Median, not mean, so the yellow line itself barely moves the estimate.
    Subsampled 4x in both axes; the Pi does this every frame.
    """
    top = min(int(frame_bgr.shape[0] * y_ratio), frame_bgr.shape[0] - 1)
    return float(np.median(frame_bgr[top::4, ::4].max(axis=2)))


def ema_update(previous, sample, alpha):
    return sample if previous is None else alpha * sample + (1.0 - alpha) * previous


def adaptive_sv_offsets(brightness, reference, s_max_offset, v_max_offset):
    """Return (s_low_offset, v_low_offset, v_high_offset), all bounded.

    Thresholds only widen in the direction the yellow moves:
      darker  -> V_low goes down (at most v_max_offset)
      brighter-> V_high goes up and, as colours wash out, S_low goes down
    H is never touched.
    """
    delta = float(brightness) - float(reference)
    v_shift = float(np.clip(ADAPT_V_GAIN * delta, -v_max_offset, v_max_offset))
    s_shift = float(np.clip(ADAPT_S_GAIN * delta, 0.0, s_max_offset))
    v_low_offset = int(round(min(v_shift, 0.0)))
    v_high_offset = int(round(max(v_shift, 0.0)))
    s_low_offset = -int(round(s_shift))
    return s_low_offset, v_low_offset, v_high_offset


def apply_sv_offsets(lower, upper, s_low_offset, v_low_offset, v_high_offset):
    """Return new (lower, upper) uint8 arrays; H copied unchanged, S/V clamped."""
    lower = np.asarray(lower, dtype=np.int32).copy()
    upper = np.asarray(upper, dtype=np.int32).copy()
    lower[1] = np.clip(lower[1] + s_low_offset, 0, upper[1])
    lower[2] = np.clip(lower[2] + v_low_offset, 0, upper[2])
    upper[2] = np.clip(upper[2] + v_high_offset, lower[2], 255)
    return lower.astype(np.uint8), upper.astype(np.uint8)


# ------------------------------------------------------------------- YAML --

_KEY_LINE = r'^(?P<head>[ \t]*{key}:[ \t]*)(?P<value>[^\s#]+)(?P<tail>.*)$'


def read_ros_params(path, node='camera_straight_drive'):
    with open(path, encoding='utf-8') as handle:
        data = yaml.safe_load(handle)
    return data[node]['ros__parameters']


def update_hsv_yaml(path, values, node='camera_straight_drive', now=None):
    """Rewrite only the six yellow HSV values in path; return (old, backup).

    Textual, line-targeted replacement keeps every comment/order/other value.
    The result is re-parsed and compared before it replaces the original
    (atomic os.replace), and a timestamped backup is written first. Any
    failure raises and leaves the original file untouched.
    """
    if set(values) != set(HSV_KEYS):
        raise ValueError(f'need exactly {HSV_KEYS}')
    with open(path, encoding='utf-8') as handle:
        original = handle.read()
    before = yaml.safe_load(original)
    params = before[node]['ros__parameters']
    old = {key: params[key] for key in HSV_KEYS}

    text = original
    for key in HSV_KEYS:
        pattern = re.compile(_KEY_LINE.format(key=re.escape(key)), re.MULTILINE)
        if len(pattern.findall(text)) != 1:
            raise ValueError(f'{key} must appear exactly once in {path}')
        text = pattern.sub(
            lambda m, v=int(values[key]): f"{m['head']}{v}{m['tail']}", text)

    after = yaml.safe_load(text)
    expected = yaml.safe_load(original)
    expected[node]['ros__parameters'].update(
        {key: int(values[key]) for key in HSV_KEYS})
    if after != expected:
        raise ValueError('YAML verification failed; original left untouched')

    stamp = (now or datetime.datetime.now()).strftime('%Y%m%d_%H%M%S')
    backup = f'{path}.bak_hsv_{stamp}'
    shutil.copy2(path, backup)
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix='.hsv_', suffix='.yaml', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(text)
        shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return old, backup
