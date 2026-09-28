"""Dev-only: MP3 -> monophonic buzzer melody (run once on a laptop, not on Pinky).

Needs ffmpeg + librosa (e.g. in a throwaway venv). Writes
pinky_media/keroro_buzzer_melody.py and a sine preview WAV.

    python3 tools/extract_buzzer_melody.py assets/keroro_song.mp3 \
        pinky_media/keroro_buzzer_melody.py /tmp/keroro

Writes KERORO_MELODY_RAW / _SMOOTH / _ULTRA_SMOOTH, one legato sine preview
per version (/tmp/keroro_buzzer_preview_<version>.wav) and the per-rest
evidence table /tmp/keroro_rest_analysis.csv.
"""

import csv
import subprocess
import sys
import wave

import numpy as np

SR = 22050
HOP = 256                 # ~11.6 ms frames
BAND_HZ = (220, 2000)     # cut bass/drum body and cymbal hiss
FMIN, FMAX = 190.0, 1600.0
MIDI_RANGE = (55, 88)     # G3..E6; outside = treated as rest
MIN_PROB = 0.05           # pyin voiced-probability floor (sweep: best repeat match)
SMOOTH_FRAMES = 5         # ~60 ms median filter against vibrato/glitches
MIN_NOTE = 0.06           # shorter notes merge into a neighbour
MIN_REST = 0.04           # shorter rests are absorbed

# smooth(): buzzer post-processing of pyin dropouts (see its docstring).
SHORT_REST = 0.20         # rests <= this are always removed
BRIDGE_REST = 0.40        # rests <= this are removed between close pitches
BRIDGE_SEMITONES = 2      # "close" = neighbours within this many semitones
GLITCH_NOTE = 0.09        # shorter notes may be pitch glitches
GLITCH_SEMITONES = 3      # glitch = sticks out >= this from both neighbours

# ultra_smooth(): evidence-based rest reconstruction for the buzzer.
NEIGHBOUR_WINDOW = 0.25   # s of audio each side a rest is compared against
EVIDENCE_PROB = 0.02      # raw pyin frames above this count as pitch evidence
ULTRA_SHORT_GAP = 0.30    # <= : filled unless there is REAL_REST evidence
ULTRA_MEDIUM_GAP = 0.60   # <= : filled if pitch continuity/evidence
ULTRA_LONG_GAP = 1.00     # <= : filled only on strong evidence; > : kept
SILENCE_RMS = 0.30        # mix RMS / melody-level RMS below this = silence
PHRASE_DROP = 0.40        # gap harmonic RMS / neighbours' below this = phrase break
MIN_HARMONIC = 0.15       # medium/long fill needs some melody-band energy
SOME_EVIDENCE = 0.10      # fraction of gap frames agreeing on one raw f0
STRONG_EVIDENCE = 0.30
ULTRA_GLITCH_NOTE = 0.11  # ultra: isolated glitches up to this are merged
MICRO_GAP = 0.08          # rests this short are joined unless REAL_REST


def load_mid(path):
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', path, '-ac', '2', '-ar', str(SR),
         '-f', 's16le', '-'], check=True, capture_output=True).stdout
    stereo = np.frombuffer(raw, np.int16).reshape(-1, 2) / 32768.0
    return stereo.mean(axis=1)  # centre (vocal/lead) channel


def frame_notes(y):
    """Return (frame MIDI melody, raw evidence dict for rest reconstruction)."""
    import librosa
    import scipy.signal as sg
    sos = sg.butter(4, BAND_HZ, btype='band', fs=SR, output='sos')
    harmonic = librosa.effects.harmonic(sg.sosfiltfilt(sos, y), margin=3.0)
    # fill_na=None keeps pyin's best f0 guess on unvoiced frames too; voiced
    # frames are identical to the default, so raw/smooth output is unchanged.
    f0, voiced, prob = librosa.pyin(
        harmonic, fmin=FMIN, fmax=FMAX, sr=SR, frame_length=2048,
        hop_length=HOP, fill_na=None)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=HOP)[0]
    harm = librosa.feature.rms(y=harmonic, frame_length=2048, hop_length=HOP)[0]
    f0_midi = np.zeros(f0.size, int)
    finite = np.isfinite(f0)
    f0_midi[finite] = np.round(librosa.hz_to_midi(f0[finite])).astype(int)
    f0_midi[(f0_midi < MIDI_RANGE[0]) | (f0_midi > MIDI_RANGE[1])] = 0
    ok = voiced & (prob >= MIN_PROB) & np.isfinite(f0)
    midi = np.zeros(f0.size, int)
    midi[ok] = np.round(librosa.hz_to_midi(f0[ok])).astype(int)
    midi[(midi < MIDI_RANGE[0]) | (midi > MIDI_RANGE[1])] = 0
    midi = sg.medfilt(midi, SMOOTH_FRAMES).astype(int)
    # Fold isolated octave errors back toward the local (0.5 s) median.
    half = int(0.25 * SR / HOP)
    for i in np.flatnonzero(midi):
        window = midi[max(0, i - half):i + half + 1]
        local = np.median(window[window > 0])
        while midi[i] - local > 9:
            midi[i] -= 12
        while local - midi[i] > 9:
            midi[i] += 12
    midi[(midi < MIDI_RANGE[0]) | (midi > MIDI_RANGE[1])] = 0
    sounding = midi > 0
    evidence = {
        'frame': HOP / SR,
        'rms': rms[:midi.size], 'harm': harm[:midi.size],
        'prob': prob, 'f0_midi': f0_midi,
        # References = typical level while the melody is actually tracked.
        'rms_ref': float(np.median(rms[:midi.size][sounding])),
        'harm_ref': float(np.median(harm[:midi.size][sounding])),
    }
    return midi, evidence


def segment(midi):
    frame = HOP / SR
    events = []  # [midi, seconds]
    for m in midi:
        if events and events[-1][0] == m:
            events[-1][1] += frame
        else:
            events.append([int(m), frame])
    changed = True
    while changed:
        changed = False
        for i, (m, d) in enumerate(events):
            if d >= (MIN_REST if m == 0 else MIN_NOTE):
                continue
            # Merge into the longer neighbour; never invent a new pitch.
            nbrs = [j for j in (i - 1, i + 1) if 0 <= j < len(events)]
            j = max(nbrs, key=lambda k: events[k][1])
            events[j][1] += d
            del events[i]
            changed = True
            break
        events = merge_same(events)
    return events


def merge_same(events):
    merged = []
    for m, d in events:
        if merged and merged[-1][0] == m:
            merged[-1][1] += d
        else:
            merged.append([m, d])
    return merged


def smooth(events, glitch_note=GLITCH_NOTE, short_rest=SHORT_REST,
           bridge_rest=BRIDGE_REST):
    """Remove pyin dropouts so the buzzer plays legato; total time is kept.

    events: [[midi, seconds]], midi 0 = rest. Only existing pitches are
    extended; no new pitch is created.
    - rest <= SHORT_REST: removed, time split half/half to its neighbours
    - rest <= BRIDGE_REST between notes within BRIDGE_SEMITONES: same
    - note < GLITCH_NOTE sticking out >= GLITCH_SEMITONES from both sounding
      neighbours (or between two equal neighbours): merged into the closer one
    - equal neighbours are merged
    Longer rests (phrase breaks) are kept.
    """
    events = merge_same([list(e) for e in events])
    changed = True
    while changed:
        changed = False
        for i, (m, d) in enumerate(events):
            prev = events[i - 1] if i > 0 else None
            nxt = events[i + 1] if i + 1 < len(events) else None
            if m == 0:
                close = (prev and nxt and prev[0] and nxt[0]
                         and abs(prev[0] - nxt[0]) <= BRIDGE_SEMITONES)
                if not (d <= short_rest or (d <= bridge_rest and close)):
                    continue
                sides = [e for e in (prev, nxt) if e and e[0]]
                if not sides:
                    continue
                for e in sides:
                    e[1] += d / len(sides)
            else:
                if d >= glitch_note or not (prev and nxt and prev[0] and nxt[0]):
                    continue
                outlier = (abs(m - prev[0]) >= GLITCH_SEMITONES
                           and abs(m - nxt[0]) >= GLITCH_SEMITONES)
                if not (outlier or prev[0] == nxt[0]):
                    continue
                target = min((prev, nxt), key=lambda e: abs(e[0] - m))
                target[1] += d
            del events[i]
            events = merge_same(events)
            changed = True
            break
    return events


def rest_features(events, ev):
    """Per-rest evidence from the raw pyin/energy frames (see ultra_smooth)."""
    frame = ev['frame']
    rows = []
    t = 0.0
    for i, (m, d) in enumerate(events):
        start, t = t, t + d
        if m:
            continue
        a, b = int(round(start / frame)), max(int(round(t / frame)), int(round(start / frame)) + 1)
        prev = events[i - 1][0] if i > 0 else 0
        nxt = events[i + 1][0] if i + 1 < len(events) else 0
        ctx = int(round(NEIGHBOUR_WINDOW / frame))
        around = np.concatenate([ev['harm'][max(0, a - ctx):a], ev['harm'][b:b + ctx]])
        harm = float(np.mean(ev['harm'][a:b]))
        # Raw f0 candidates the tracker rejected, folded toward the neighbours.
        ref = np.mean([p for p in (prev, nxt) if p]) if (prev or nxt) else 0
        cand = ev['f0_midi'][a:b][(ev['prob'][a:b] >= EVIDENCE_PROB)
                                  & (ev['f0_midi'][a:b] > 0)].astype(float)
        if ref:
            cand = cand - 12 * np.round((cand - ref) / 12)
        evid_midi = int(np.bincount(cand.astype(int)).argmax()) if cand.size else 0
        evid_frac = float(np.mean(cand == evid_midi) * cand.size / (b - a)) if cand.size else 0.0
        rows.append({
            'index': i, 'start_sec': round(start, 3), 'duration_sec': round(d, 3),
            'prev_midi': prev, 'next_midi': nxt,
            'semitone_gap': abs(prev - nxt) if prev and nxt else None,
            'mean_rms': round(float(np.mean(ev['rms'][a:b])) / ev['rms_ref'], 3),
            'mean_harmonic_energy': round(harm / ev['harm_ref'], 3),
            'harmonic_drop': round(harm / float(np.mean(around)), 3) if around.size else 0.0,
            'mean_voiced_probability': round(float(np.mean(ev['prob'][a:b])), 3),
            'raw_f0_evidence': round(evid_frac, 3), 'evidence_midi': evid_midi,
        })
    return rows


def classify_rest(r):
    """Return (classification, action) for one rest_features() row.

    Energy never drops in this march (accompaniment runs through vocal
    breaks), so a phrase break is detected from the melody band itself: a
    harmonic-energy drop against the neighbouring notes. Duration only sets
    how much pitch evidence a fill needs.
    """
    prev, nxt, d = r['prev_midi'], r['next_midi'], r['duration_sec']
    evid, em = r['raw_f0_evidence'], r['evidence_midi']
    if not (prev and nxt):
        return 'REAL_REST', 'keep: song edge'
    if r['mean_rms'] < SILENCE_RMS:
        return 'REAL_REST', 'keep: silence'
    if r['harmonic_drop'] < PHRASE_DROP:
        return 'REAL_REST', 'keep: phrase boundary (harmonic drop)'
    if d > ULTRA_LONG_GAP:
        return 'REAL_REST', 'keep: longer than ULTRA_LONG_GAP'
    jump = abs(prev - nxt)
    near = bool(em) and min(abs(em - prev), abs(em - nxt)) <= 1
    strong = evid >= STRONG_EVIDENCE or (jump <= 2 and evid >= SOME_EVIDENCE and near)
    if d <= ULTRA_SHORT_GAP:
        ok = jump <= 5 or evid >= SOME_EVIDENCE
    elif d <= ULTRA_MEDIUM_GAP:
        ok = r['mean_harmonic_energy'] >= MIN_HARMONIC and (
            jump <= 2 or (jump <= 5 and evid >= SOME_EVIDENCE) or strong)
    else:
        ok = r['mean_harmonic_energy'] >= MIN_HARMONIC and strong
    if not ok:
        return 'UNCERTAIN', 'keep: weak evidence'
    if prev == nxt:
        return 'LIKELY_DROPOUT', 'fill: same note'
    if evid >= SOME_EVIDENCE and em in (prev, nxt):
        return 'LIKELY_DROPOUT', 'fill: extend ' + ('prev' if em == prev else 'next')
    if evid >= STRONG_EVIDENCE and em and min(prev, nxt) - 2 <= em <= max(prev, nxt) + 2:
        return 'LIKELY_DROPOUT', 'fill: raw f0 note'
    return 'LIKELY_DROPOUT', 'fill: split'


def ultra_smooth(events, ev):
    """smooth() output + evidence-based dropout fill. Returns (events, rows)."""
    rows = rest_features(events, ev)
    out = [list(e) for e in events]
    for r in reversed(rows):  # right-to-left keeps earlier indices valid
        r['classification'], r['action'] = classify_rest(r)
        i, action = r['index'], r['action']
        d = out[i][1]
        if not action.startswith('fill'):
            continue
        if action == 'fill: raw f0 note':
            out[i][0] = r['evidence_midi']
            continue
        if action in ('fill: same note', 'fill: extend prev'):
            out[i - 1][1] += d
        elif action == 'fill: extend next':
            out[i + 1][1] += d
        else:
            out[i - 1][1] += d / 2
            out[i + 1][1] += d / 2
        del out[i]
    out = smooth(merge_same(out), glitch_note=ULTRA_GLITCH_NOTE,
                 short_rest=MICRO_GAP, bridge_rest=MICRO_GAP)
    return out, rows


def midi_to_hz(m):
    return 0 if m == 0 else int(round(440.0 * 2 ** ((m - 69) / 12)))


def write_module(melodies, path, duration):
    lines = [
        '"""Keroro march lead melody for pinkylib.Buzzer (generated, do not edit).',
        '',
        'Source: assets/keroro_song.mp3 via tools/extract_buzzer_melody.py',
        f'(source length {duration:.1f}s). (frequency_hz, duration_sec); 0 = rest.',
        'RAW: pyin notes. SMOOTH: pyin dropouts <= 0.2-0.4 s removed.',
        'ULTRA_SMOOTH: SMOOTH + rests classified from raw pyin/energy evidence',
        'and likely dropouts filled (phrase breaks and silences kept).',
        '"""',
    ]
    for name, melody in melodies.items():
        lines += ['', f'KERORO_MELODY_{name.upper()} = [']
        lines += [f'    ({f}, {d}),' for f, d in melody]
        lines += [']']
    lines += ['', 'KERORO_MELODY = KERORO_MELODY_SMOOTH', '']
    with open(path, 'w') as out:
        out.write('\n'.join(lines))


def stats(melody):
    f = np.array([x[0] for x in melody])
    d = np.array([x[1] for x in melody])
    rest = d[f == 0].sum()
    return {
        'events': len(melody), 'notes': int((f > 0).sum()),
        'rests': int((f == 0).sum()), 'rest time': round(float(rest), 2),
        'rest ratio': f'{rest / d.sum():.1%}',
        'median note': round(float(np.median(d[f > 0])), 3),
        'note->note': sum(1 for a, b in zip(f, f[1:]) if a and b),
        'duration': round(float(d.sum()), 2),
    }


def write_preview(melody, path, rate=22050):
    # Legato like the buzzer: continuous phase, silence only on rests.
    freq = np.concatenate(
        [np.full(int(round(d * rate)), f, float) for f, d in melody])
    phase = np.cumsum(2 * np.pi * freq / rate)
    gate = np.convolve((freq > 0).astype(float),
                       np.ones(int(0.005 * rate)) / int(0.005 * rate), 'same')
    pcm = (0.3 * gate * np.sin(phase) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(pcm.tobytes())


def main(mp3, module_path, out_prefix='/tmp/keroro'):
    y = load_mid(mp3)
    midi, ev = frame_notes(y)
    raw = segment(midi)
    smooth_events = smooth(raw)
    ultra, rows = ultra_smooth(smooth_events, ev)
    melodies = {
        name: [(midi_to_hz(m), round(d, 3)) for m, d in events]
        for name, events in (('raw', raw), ('smooth', smooth_events),
                             ('ultra_smooth', ultra))}
    write_module(melodies, module_path, y.size / SR)
    for name, melody in melodies.items():
        write_preview(melody, f'{out_prefix}_buzzer_preview_{name}.wav')
    columns = ['start_sec', 'duration_sec', 'prev_midi', 'next_midi',
               'semitone_gap', 'mean_rms', 'mean_harmonic_energy',
               'harmonic_drop', 'mean_voiced_probability', 'raw_f0_evidence',
               'evidence_midi', 'classification', 'action']
    with open(f'{out_prefix}_rest_analysis.csv', 'w', newline='') as out:
        writer = csv.DictWriter(out, columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    table = {name: stats(m) for name, m in melodies.items()}
    print(f'source {y.size / SR:.2f}s')
    print(f'{"":14}' + ''.join(f'{n:>14}' for n in table))
    for key in table['raw']:
        print(f'{key:14}' + ''.join(f'{str(t[key]):>14}' for t in table.values()))
    for label in ('REAL_REST', 'LIKELY_DROPOUT', 'UNCERTAIN'):
        group = [r for r in rows if r['classification'] == label]
        print(f'{label}: {len(group)} (>=0.4s: '
              f'{sum(r["duration_sec"] >= 0.4 for r in group)})')
    actions = {}
    for r in rows:
        actions[r['action']] = actions.get(r['action'], 0) + 1
    print(actions)


if __name__ == '__main__':
    main(*sys.argv[1:4])
