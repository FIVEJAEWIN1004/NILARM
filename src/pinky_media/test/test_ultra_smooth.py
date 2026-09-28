"""ultra_smooth(): rests classified from synthetic pyin/energy evidence."""

import importlib.util
import pathlib

import numpy as np
import pytest

from pinky_media.keroro_buzzer_melody import (
    KERORO_MELODY_RAW, KERORO_MELODY_ULTRA_SMOOTH)

_TOOL = pathlib.Path(__file__).resolve().parents[1] / 'tools' / 'extract_buzzer_melody.py'
_spec = importlib.util.spec_from_file_location('extract_buzzer_melody', _TOOL)
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

G4, A4, B4, G5 = 67, 69, 71, 79
FRAME = 0.01


def evidence(events, **gap):
    """Flat 'music playing' evidence; `gap` overrides frames of the one rest."""
    n = int(round(sum(d for _, d in events) / FRAME)) + 1
    ev = {'frame': FRAME, 'rms': np.ones(n), 'harm': np.ones(n),
          'prob': np.full(n, 0.01), 'f0_midi': np.zeros(n, int),
          'rms_ref': 1.0, 'harm_ref': 1.0}
    start = events[0][1]
    a, b = int(round(start / FRAME)), int(round((start + events[1][1]) / FRAME))
    for key, value in gap.items():
        ev[key][a:b] = value
    return ev


def run(events, **gap):
    out, rows = E.ultra_smooth(events, evidence(events, **gap))
    assert sum(d for _, d in out) == pytest.approx(sum(d for _, d in events))
    return out, rows


def test_half_second_rest_with_strong_voiced_evidence_is_restored():
    out, rows = run([[G4, 1.0], [0, 0.5], [B4, 1.0]], f0_midi=A4, prob=0.5)
    assert rows[0]['classification'] == 'LIKELY_DROPOUT'
    assert [m for m, _ in out] == [G4, A4, B4]  # A4 comes from the raw f0


def test_short_rest_in_true_silence_is_kept():
    out, rows = run([[G4, 1.0], [0, 0.2], [G4, 1.0]], rms=0.05, harm=0.02)
    assert rows[0]['classification'] == 'REAL_REST'
    assert [m for m, _ in out] == [G4, 0, G4]


def test_dropout_between_same_notes_is_filled():
    out, _ = run([[G4, 1.0], [0, 0.5], [G4, 1.0]])
    assert out == [[G4, pytest.approx(2.5)]]


def test_gap_in_smooth_contour_is_filled():
    out, _ = run([[G4, 1.0], [0, 0.45], [A4, 1.0]])
    assert [m for m, _ in out] == [G4, A4]


def test_big_jump_without_evidence_keeps_rest():
    out, rows = run([[G4, 1.0], [0, 0.5], [G5, 1.0]])
    assert rows[0]['classification'] == 'UNCERTAIN'
    assert [m for m, _ in out] == [G4, 0, G5]


def test_phrase_boundary_keeps_rest():
    # Accompaniment continues (RMS 1) but the melody band drops away.
    out, rows = run([[G4, 1.0], [0, 0.25], [G4, 1.0]], harm=0.2)
    assert rows[0]['action'] == 'keep: phrase boundary (harmonic drop)'
    assert [m for m, _ in out] == [G4, 0, G4]


def test_generated_ultra_smooth_keeps_source_length():
    total = sum(d for _, d in KERORO_MELODY_ULTRA_SMOOTH)
    assert total == pytest.approx(sum(d for _, d in KERORO_MELODY_RAW), abs=0.1)
    assert all(f == 0 or 1 <= f <= 10000 for f, _ in KERORO_MELODY_ULTRA_SMOOTH)
