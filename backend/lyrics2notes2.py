import librosa
import numpy as np
from collections import Counter
import json
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
import tkinter as tk
from tkinter import filedialog

# Try to import partitura for MusicXML conversion
try:
    import partitura
    from partitura.io import exportmusicxml
    PARTITURA_AVAILABLE = True
    print("✅ partitura available for MusicXML conversion")
except ImportError:
    PARTITURA_AVAILABLE = False
    print("⚠️ partitura not available - MIDI only")

# ---------------- Melody Extraction ---------------- #

def extract_main_melody_line(vocals_path, tempo_bpm=139):
    """
    Extract only the main melodic line - like what a human would sing along to.
    Focus on prominent, stable pitches and ignore embellishments.
    """
    print("🎵 MAIN MELODY LINE EXTRACTOR")
    print("=" * 40)

    # Load audio
    y, sr = librosa.load(vocals_path)
    print(f"📊 Audio: {len(y)/sr:.1f} seconds")

    beat_duration = 60 / tempo_bpm
    chunk_duration = beat_duration
    chunk_samples = int(chunk_duration * sr)

    melody_notes = []

    # Process audio in beat-sized chunks
    for start_sample in range(0, len(y) - chunk_samples, chunk_samples):
        end_sample = start_sample + chunk_samples
        chunk = y[start_sample:end_sample]
        start_time = start_sample / sr

        if np.max(np.abs(chunk)) < 0.01:
            continue

        f0_chunk, voiced, confidence = librosa.pyin(
            chunk,
            fmin=librosa.note_to_hz("C3"),
            fmax=librosa.note_to_hz("C6"),
            hop_length=256,
        )

        valid_pitches = f0_chunk[~np.isnan(f0_chunk)]
        valid_confidence = confidence[~np.isnan(f0_chunk)]

        if len(valid_pitches) < len(f0_chunk) * 0.25:
            continue

        midi_pitches = [librosa.hz_to_midi(f) for f in valid_pitches]
        midi_pitches = [round(m) for m in midi_pitches if 36 <= m <= 84]

        if midi_pitches:
            pitch_counts = Counter(midi_pitches)
            most_common_pitch = pitch_counts.most_common(1)[0][0]
            if pitch_counts[most_common_pitch] >= len(midi_pitches) * 0.3:
                melody_notes.append(
                    {"start": start_time, "note": most_common_pitch}
                )

    print(f"🎼 Found {len(melody_notes)} melody chunks")

    # Group consecutive identical notes
    grouped_notes = []
    i = 0
    while i < len(melody_notes):
        current_note = melody_notes[i]["note"]
        start_time = melody_notes[i]["start"]
        end_time = start_time + chunk_duration

        j = i + 1
        while (
            j < len(melody_notes)
            and melody_notes[j]["note"] == current_note
            and melody_notes[j]["start"] - end_time < 0.2
        ):
            end_time = melody_notes[j]["start"] + chunk_duration
            j += 1

        duration = end_time - start_time
        if duration >= beat_duration * 0.5:
            grouped_notes.append(
                {"start": start_time, "end": end_time, "note": current_note}
            )

        i = j

    print(f"🎵 Grouped into {len(grouped_notes)} notes")

    # Convert to beats
    notes = []
    for g in grouped_notes:
        duration_beats = (g["end"] - g["start"]) / beat_duration
        notes.append(
            {
                "start": g["start"],
                "end": g["end"],
                "note": g["note"],
                "duration_beats": duration_beats,
            }
        )

    # Snap to fixed grid
    notes = quantize_to_fixed_grid(notes, tempo_bpm)

    # Clean up tiny micro-notes
    print("🧹 Cleaning tiny notes...")
    notes = clean_tiny_notes(notes, tempo_bpm, min_keep=0.25)

    return notes

# ---------------- Helpers ---------------- #

def quantize_to_fixed_grid(notes, tempo_bpm=139):
    """
    Force notes to align with a consistent rhythmic grid.
    """
    beat_duration = 60 / tempo_bpm
    standard_beats = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]  # 16th through whole

    def q_start(t): return round(t / (beat_duration / 4)) * (beat_duration / 4)
    def q_dur(d): return min(standard_beats, key=lambda x: abs(x - d)) * beat_duration

    fixed = []
    for n in notes:
        qs = q_start(n["start"])
        qd = q_dur(n["duration_beats"])
        fixed.append(
            {"start": qs, "end": qs + qd, "note": n["note"], "duration_beats": qd}
        )

    return fixed

def clean_tiny_notes(notes, tempo_bpm=139, min_keep=0.25):
    """
    Remove or extend tiny notes:
      - If < min_keep beats and isolated, extend to 8th or quarter.
      - If < min_keep beats and in dense section, delete it.
    """
    if not notes:
        return notes

    beat_duration = 60 / tempo_bpm
    cleaned = []

    for i, note in enumerate(notes):
        if note["duration_beats"] < min_keep:
            prev_gap = None
            next_gap = None
            if i > 0:
                prev_gap = note["start"] - notes[i - 1]["end"]
            if i < len(notes) - 1:
                next_gap = notes[i + 1]["start"] - note["end"]

            is_isolated = (
                (prev_gap is None or prev_gap > beat_duration)
                and (next_gap is None or next_gap > beat_duration)
            )

            if is_isolated:
                note["duration_beats"] = 1.0
                note["end"] = note["start"] + beat_duration
                cleaned.append(note)
            else:
                continue
        else:
            cleaned.append(note)

    print(f"✅ Cleaned down to {len(cleaned)} notes")
    return cleaned

# ---------------- MIDI + MusicXML ---------------- #

def create_simple_midi(notes, tempo_bpm=139):
    if not notes:
        return None

    midi_file = MidiFile(ticks_per_beat=480)
    track = MidiTrack()
    midi_file.tracks.append(track)

    tempo = bpm2tempo(tempo_bpm)
    track.append(MetaMessage("set_tempo", tempo=tempo, time=0))
    track.append(MetaMessage("track_name", name="Main Melody", time=0))

    beat_duration = 60 / tempo_bpm
    current_tick = 0

    for note in notes:
        start_tick = int((note["start"] / beat_duration) * 480)
        duration_ticks = int(note["duration_beats"] * 480)
        delta = max(0, start_tick - current_tick)

        track.append(Message("note_on", note=note["note"], velocity=80, time=delta))
        track.append(Message("note_off", note=note["note"], velocity=0, time=duration_ticks))

        current_tick = start_tick + duration_ticks

    midi_path = "main_melody.mid"
    midi_file.save(midi_path)
    print(f"💾 Saved MIDI: {midi_path}")
    return midi_path

def create_musicxml_from_midi(midi_path):
    if not PARTITURA_AVAILABLE:
        return None
    try:
        score = partitura.load_score(midi_path)
        xml_path = "main_melody.musicxml"
        exportmusicxml.save_musicxml(score, xml_path)
        print(f"💾 Saved MusicXML: {xml_path}")
        return xml_path
    except Exception as e:
        print(f"⚠️ MusicXML export failed: {e}")
        return None

# ---------------- Main ---------------- #

def main():
    root = tk.Tk()
    root.withdraw()
    vocals_path = filedialog.askopenfilename(
        title="Select vocals audio file",
        filetypes=[("Audio", "*.wav *.mp3 *.flac *.m4a"), ("All", "*.*")]
    )
    if not vocals_path:
        return

    tempo_bpm = 139
    notes = extract_main_melody_line(vocals_path, tempo_bpm)

    if not notes:
        print("❌ No notes extracted")
        return

    with open("main_melody.json", "w") as f:
        json.dump({"tempo_bpm": tempo_bpm, "notes": notes}, f, indent=2)

    midi_file = create_simple_midi(notes, tempo_bpm)
    if midi_file:
        create_musicxml_from_midi(midi_file)

    print("\n🎉 Done!")

if __name__ == "__main__":
    main()
