"""Loop KERORO_MELODY on the Pinky buzzer: /pinky/music_control START/STOP."""

import signal
import threading

import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import String

from pinky_media.keroro_buzzer_melody import (
    KERORO_MELODY_RAW, KERORO_MELODY_SMOOTH, KERORO_MELODY_ULTRA_SMOOTH)

MELODIES = {
    'raw': KERORO_MELODY_RAW,
    'smooth': KERORO_MELODY_SMOOTH,
    'ultra_smooth': KERORO_MELODY_ULTRA_SMOOTH,
}
ARTICULATION_GAP = 0.03  # legato_mode=false silence at the end of each note
SUSTAIN_MAX_REST = 0.6   # sustain never eats into rests longer than this
MICRO_GAP = 0.08         # a rest left shorter than this by sustain is joined


def apply_sustain(melody, ratio):
    """Lengthen notes into the following short rest only.

    A note of d seconds may take up to d * (ratio - 1) from the rest after it;
    the next note still starts at its original time. Rests longer than
    SUSTAIN_MAX_REST (phrase breaks) are left untouched.
    """
    if ratio <= 1.0:
        return list(melody)
    out = []
    for freq, dur in melody:
        if not freq and out and out[-1][0] and dur <= SUSTAIN_MAX_REST:
            take = min(dur, out[-1][1] * (ratio - 1.0))
            if dur - take < MICRO_GAP:
                take = dur
            out[-1] = (out[-1][0], out[-1][1] + take)
            dur -= take
            if dur <= 0:
                continue
        out.append((freq, dur))
    return out


def make_buzzer():
    # Imported lazily so the node can be imported/tested off-robot.
    from pinkylib import Buzzer
    return Buzzer()


class BuzzerPlayer(Node):

    def __init__(self, melody=None):
        super().__init__('pinky_buzzer_player')
        self.declare_parameter('melody_mode', 'smooth')
        # >1.0 lets each note ring into the short rest after it (e.g. 1.08).
        self.declare_parameter('sustain_ratio', 1.0)
        self._mode = str(self.get_parameter('melody_mode').value)
        if melody is None:
            if self._mode not in MELODIES:
                self.get_logger().error(
                    f'unknown melody_mode {self._mode!r}; using smooth '
                    f'(choices: {", ".join(MELODIES)})')
                self._mode = 'smooth'
            melody = MELODIES[self._mode]
        melody = apply_sustain(
            melody, float(self.get_parameter('sustain_ratio').value))
        self.declare_parameter('buzzer_duty', 30)
        # Piezo buzzers are quiet at low Hz; +1 plays an octave higher.
        self.declare_parameter('octave_shift', 0)
        # true: note->note changes only frequency. false: every note ends
        # with a short duty-0 gap (detached articulation, for comparison).
        self.declare_parameter('legato_mode', True)
        self._legato = bool(self.get_parameter('legato_mode').value)
        self._duty = min(99, max(0, int(self.get_parameter('buzzer_duty').value)))
        shift = 2.0 ** int(self.get_parameter('octave_shift').value)
        self._melody = [
            (min(10000, max(1, int(round(freq * shift)))) if freq else 0, dur)
            for freq, dur in melody]
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._worker = None
        self._buzzer = None
        self._started = False
        try:
            self._buzzer = make_buzzer()
            self._buzzer.buzzer_start()  # PWM running at duty 0 = silent
            self._started = True
        except Exception as error:
            self.get_logger().error(f'buzzer unavailable; playback disabled: {error}')
        self.create_subscription(
            String, '/pinky/music_control', self._on_control, 10)
        self.get_logger().info(
            f'buzzer player ready (idle until START): {len(self._melody)} events, '
            f'mode={self._mode}, duty={self._duty}, legato={self._legato}, '
            f'sustain={self.get_parameter("sustain_ratio").value}')

    def _on_control(self, message):
        command = message.data.strip().upper()
        if command == 'START':
            self._start()
        elif command == 'STOP':
            self._halt()
            self.get_logger().info('buzzer STOP')
        else:
            self.get_logger().warning(f'unknown music command: {message.data!r}')

    def _start(self):
        if self._buzzer is None:
            self.get_logger().error('buzzer unavailable; START ignored')
            return
        if self._worker is not None and self._worker.is_alive():
            if not self._stop.is_set():
                self.get_logger().info('already playing; START ignored')
                return
            self._worker.join(timeout=1.0)  # previous STOP still unwinding
        self._stop = threading.Event()
        self._worker = threading.Thread(
            target=self._play, args=(self._stop,), daemon=True)
        self._worker.start()
        self.get_logger().info('buzzer START')

    def _set(self, stop, freq=None, duty=None):
        with self._lock:
            if stop.is_set():
                return False
            if freq is not None:
                self._buzzer.set_buzzer_freq(freq)
            if duty is not None:
                self._buzzer.set_buzzer_duty(duty)
            return True

    def _play(self, stop):
        sounding = False
        try:
            while not stop.is_set():
                for freq, duration in self._melody:
                    if not freq:
                        if sounding and not self._set(stop, duty=0):
                            break
                        sounding = False
                        stop.wait(duration)
                        continue
                    # Legato: note->note only changes frequency; duty is
                    # (re)applied only when coming out of silence.
                    if not self._set(stop, freq, None if sounding else self._duty):
                        break
                    sounding = True
                    if self._legato:
                        stop.wait(duration)  # STOP wakes this immediately
                        continue
                    gap = min(ARTICULATION_GAP, duration / 2)
                    stop.wait(duration - gap)
                    if not self._set(stop, duty=0):
                        break
                    sounding = False
                    stop.wait(gap)
        except Exception as error:
            self.get_logger().error(f'buzzer playback failed: {error}')
        finally:
            self._silence()

    def _silence(self):
        if self._buzzer is None:
            return
        with self._lock:
            try:
                self._buzzer.set_buzzer_duty(0)
            except Exception as error:
                self.get_logger().error(f'buzzer duty 0 failed: {error}')

    def _halt(self):
        self._stop.set()
        self._silence()

    def destroy_node(self):
        self._halt()
        if self._worker is not None:
            self._worker.join(timeout=1.0)
        if self._buzzer is not None and self._started:
            try:
                self._buzzer.close()  # releases GPIO so the next run can claim it
            except Exception as error:
                self.get_logger().error(f'buzzer close failed: {error}')
            self._buzzer = None
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    # SIGTERM (ros2 launch / kill) takes the same cleanup path as Ctrl+C.
    signal.signal(signal.SIGTERM, signal.default_int_handler)
    node = BuzzerPlayer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
