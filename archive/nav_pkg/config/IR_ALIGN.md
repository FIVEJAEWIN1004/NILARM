# Pinky IR final alignment

The node is inactive by default. It reads and publishes sensor values while
inactive, but it only publishes velocity commands after `/ir_align/enable` is
called with `data: true`.

## Calibrate the floor values

Run this on Pinky and record several readings over both the white floor and the
brown STOP area:

```bash
python3 - <<'PY'
import time
from pinkylib import IR

ir = IR()
for _ in range(50):
    print(ir.read_ir())
    time.sleep(0.05)
PY
```

Set `dark_threshold` in `ir_align_params.yaml` near the midpoint between the
two measured ranges. Keep `dark_is_low: true` if the brown surface produces
smaller values; set it to `false` if it produces larger values. The default
threshold is deliberately invalid, so an uncalibrated node cannot move Pinky.

## Command ownership

Do not enable IR alignment while Nav2 can still command `/cmd_vel`. For the
initial independent test, finish/cancel the Nav2 task and deactivate its command
output before enabling this node. A later production integration should route
the smoothed Nav2 command and the IR command through a velocity multiplexer so
that the multiplexer is the only `/cmd_vel` publisher.

## Intended mission sequence

1. Nav2 completes the coarse STOP pose.
2. The mission coordinator gives command ownership to IR alignment.
3. It calls `/ir_align/enable` with `true`.
4. It waits for `/ir_align/aligned` to become `true`.
5. It disables alignment before restoring Nav2 command ownership.

The default center signature is bright-dark-bright. Set
`all_dark_is_centered: true` only if calibration on the real STOP marker shows
that all three sensors are over the desired center. Three lateral sensors alone
cannot determine the geometric center of a uniform two-dimensional rectangle
from one reading, so the marker signature must be confirmed on the real field.
