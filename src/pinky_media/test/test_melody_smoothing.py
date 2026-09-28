"""smooth() post-processing: dropouts removed, phrase rests kept, time kept."""

import importlib.util
import pathlib

import pytest

from pinky_media.keroro_buzzer_melody import KERORO_MELODY

_TOOL = pathlib.Path(__file__).resolve().parents[1] / 'tools' / 'extract_buzzer_melody.py'
_spec = importlib.util.spec_from_file_location('extract_buzzer_melody', _TOOL)
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

G4, A4 = 67, 69


def total(events):
    return sum(d for _, d in events)


def test_short_rest_between_same_notes_becomes_one_note():
    out = E.smooth([[G4, 0.30], [0, 0.08], [G4, 0.25]])
    assert out == [[G4, pytest.approx(0.63)]]


def test_short_rest_between_different_notes_split_and_time_kept():
    src = [[G4, 0.30], [0, 0.08], [A4, 0.25]]
    out = E.smooth(src)
    assert [m for m, _ in out] == [G4, A4]
    assert out[0][1] == pytest.approx(0.34) and out[1][1] == pytest.approx(0.29)
    assert total(out) == pytest.approx(total(src))


def test_medium_rest_bridged_only_between_close_pitches():
    assert [m for m, _ in E.smooth([[G4, 0.3], [0, 0.3], [A4, 0.3]])] == [G4, A4]
    far = [[G4, 0.3], [0, 0.3], [G4 + 7, 0.3]]
    assert [m for m, _ in E.smooth(far)] == [G4, 0, G4 + 7]


def test_long_rest_kept():
    src = [[G4, 0.3], [0, 0.6], [G4, 0.3]]
    assert E.smooth(src) == src


def test_glitch_note_merged_but_fast_scale_kept():
    glitch = E.smooth([[G4, 0.3], [G4 + 5, 0.05], [G4, 0.3]])
    assert glitch == [[G4, pytest.approx(0.65)]]
    scale = [[G4, 0.08], [G4 + 2, 0.08], [G4 + 4, 0.08]]
    assert E.smooth(scale) == scale


def test_generated_melody_keeps_source_length():
    # Source MP3 is 180.3 s; smoothing must only redistribute time.
    assert total(KERORO_MELODY) == pytest.approx(180.27, abs=0.1)
    assert all(f == 0 or 1 <= f <= 10000 for f, _ in KERORO_MELODY)
