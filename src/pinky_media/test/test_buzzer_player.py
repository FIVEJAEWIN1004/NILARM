"""No-hardware check with a fake Buzzer: one worker, loops, instant STOP, cleanup."""

import time

import pytest

import rclpy
from std_msgs.msg import String

from pinky_media import buzzer_player
from pinky_media.keroro_buzzer_melody import KERORO_MELODY


class FakeBuzzer:
    def __init__(self):
        self.calls = []

    def buzzer_start(self):
        self.calls.append(('start',))

    def set_buzzer_freq(self, freq):
        self.calls.append(('freq', freq))

    def set_buzzer_duty(self, duty):
        self.calls.append(('duty', duty))

    def close(self):
        self.calls.append(('close',))


def test_melody_data_is_buzzer_safe():
    assert KERORO_MELODY
    for freq, dur in KERORO_MELODY:
        assert freq == 0 or 1 <= freq <= 10000
        assert dur > 0


def test_start_loop_stop_close(monkeypatch):
    fake = FakeBuzzer()
    monkeypatch.setattr(buzzer_player, 'make_buzzer', lambda: fake)
    rclpy.init()
    try:
        node = buzzer_player.BuzzerPlayer(melody=[(440, 0.02), (0, 0.02)])
        node._on_control(String(data='START'))
        worker = node._worker
        node._on_control(String(data='START'))
        assert node._worker is worker  # duplicate START ignored
        time.sleep(0.3)
        assert fake.calls.count(('freq', 440)) >= 3  # melody repeated

        node._melody = [(440, 10.0)]  # long note: STOP must not wait for it
        node._on_control(String(data='STOP'))
        node._on_control(String(data='START'))
        time.sleep(0.05)
        t0 = time.monotonic()
        node._on_control(String(data='STOP'))
        node._worker.join(timeout=1.0)
        assert time.monotonic() - t0 < 0.2
        assert not node._worker.is_alive()
        assert fake.calls[-1] == ('duty', 0)

        node.destroy_node()
        assert fake.calls[-1] == ('close',)
    finally:
        rclpy.shutdown()


def _first_pass_calls(monkeypatch, legato):
    fake = FakeBuzzer()
    monkeypatch.setattr(buzzer_player, 'make_buzzer', lambda: fake)
    rclpy.init()
    try:
        node = buzzer_player.BuzzerPlayer(
            melody=[(392, 0.05), (440, 0.05), (494, 0.05), (0, 0.5)])
        node._legato = legato
        node._on_control(String(data='START'))
        time.sleep(0.3)  # inside the trailing rest of pass 1
        node._on_control(String(data='STOP'))
        assert fake.calls[-1] == ('duty', 0)  # STOP silences immediately
        node.destroy_node()
    finally:
        rclpy.shutdown()
    calls = fake.calls[1:]  # drop buzzer_start
    return calls[:calls.index(('freq', 494)) + 1]


def test_legato_note_to_note_changes_only_frequency(monkeypatch):
    calls = _first_pass_calls(monkeypatch, legato=True)
    assert calls == [('freq', 392), ('duty', 30), ('freq', 440), ('freq', 494)]


def test_non_legato_inserts_duty_zero_between_notes(monkeypatch):
    calls = _first_pass_calls(monkeypatch, legato=False)
    assert calls.count(('duty', 0)) == 2


@pytest.mark.parametrize('mode, expected', [
    (None, 'smooth'), ('raw', 'raw'), ('ultra_smooth', 'ultra_smooth'),
    ('bogus', 'smooth')])
def test_melody_mode_selects_dataset(monkeypatch, mode, expected):
    monkeypatch.setattr(buzzer_player, 'make_buzzer', FakeBuzzer)
    args = ['--ros-args', '-p', f'melody_mode:={mode}'] if mode else None
    rclpy.init(args=args)
    try:
        node = buzzer_player.BuzzerPlayer()
        assert node._mode == expected
        assert node._melody == list(buzzer_player.MELODIES[expected])
        node.destroy_node()
    finally:
        rclpy.shutdown()


def _note_starts(melody):
    starts, t = [], 0.0
    for freq, dur in melody:
        if freq:
            starts.append(round(t, 6))
        t += dur
    return starts, t


def test_sustain_eats_short_rest_but_keeps_next_note_start():
    out = buzzer_player.apply_sustain(
        [(392, 0.3), (0, 0.2), (440, 0.3), (0, 1.0), (494, 0.3)], 1.1)
    assert out[0] == (392, pytest.approx(0.33)) and out[1] == (0, pytest.approx(0.17))
    assert (0, 1.0) in out  # phrase-length rest untouched

    melody = buzzer_player.MELODIES['ultra_smooth']
    before, total = _note_starts(melody)
    after, total_after = _note_starts(buzzer_player.apply_sustain(melody, 1.1))
    assert after == pytest.approx(before, abs=1e-6)
    assert total_after == pytest.approx(total)
