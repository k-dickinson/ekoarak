import librosa
import numpy as np
from scipy import signal
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

def extract_main_melody_line(vocals_path, tempo_bpm=148):
    """
    Extract only the main melodic line - like what a human would sing along to
    Focus on prominent, stable pitches and ignore embellishments
    """
    print("🎵 MAIN MELODY LINE EXTRACTOR")
    print("=" * 40)
    print("🎯 Focusing on the main singable melody...")

    # Load audio
    y, sr = librosa.load(vocals_path)
    print(f"📊 Audio: {len(y)/sr:.1f} seconds")

    # Use larger analysis windows for stability
    beat_duration = 60 / tempo_bpm

    # Analyze in full beat chunks for smoother notes
    chunk_duration = beat_duration  # Full beat analysis windows
    chunk_samples = int(chunk_duration * sr)

    print(f"🔍 Analyzing in {chunk_duration:.3f}s chunks ({chunk_samples} samples each)")

    melody_notes = []

    # Process audio in chunks
    for start_sample in range(0, len(y) - chunk_samples, chunk_samples):
        end_sample = start_sample + chunk_samples
        chunk = y[start_sample:end_sample]
        start_time = start_sample / sr

        # Skip very quiet sections
        if np.max(np.abs(chunk)) < 0.01:
            continue

        # Extract pitch for this chunk
        f0_chunk, voiced, confidence = librosa.pyin(
            chunk,
            fmin=librosa.note_to_hz('C3'),
            fmax=librosa.note_to_hz('C6'),
            hop_length=256  # Slightly larger hop for smoother pitch
        )

        # Find the most stable/prominent pitch in this chunk
        valid_pitches = f0_chunk[~np.isnan(f0_chunk)]
        valid_confidence = confidence[~np.isnan(f0_chunk)]

        if len(valid_pitches) < len(f0_chunk) * 0.25:  # Less than 25% voiced
            continue

        # Weight pitches by confidence and frequency of occurrence
        if len(valid_pitches) > 0:
            # Convert to MIDI notes
            midi_pitches = [librosa.hz_to_midi(f) for f in valid_pitches]
            midi_pitches = [round(m) for m in midi_pitches if 36 <= m <= 84]

            if midi_pitches:
                # Find most common pitch in this chunk (the stable melody note)
                pitch_counts = Counter(midi_pitches)
                most_common_pitch = pitch_counts.most_common(1)[0][0]

                # Only add if this pitch is significantly present
                if pitch_counts[most_common_pitch] >= len(midi_pitches) * 0.3:
                    melody_notes.append({
                        'start': start_time,
                        'note': most_common_pitch,
                        'confidence': pitch_counts[most_common_pitch] / len(midi_pitches)
                    })

    print(f"🎼 Found {len(melody_notes)} melody chunks")

    if not melody_notes:
        print("❌ No stable melody found!")
        return []

    # Group consecutive identical notes, allow small gaps for legato
    print("🔗 Grouping consecutive notes (with legato)...")
    grouped_notes = []
    i = 0
    while i < len(melody_notes):
        current_note = melody_notes[i]['note']
        start_time = melody_notes[i]['start']
        end_time = start_time + chunk_duration

        # Merge consecutive notes of the same pitch, allow small gaps (up to 0.2s)
        j = i + 1
        while (j < len(melody_notes) and
               melody_notes[j]['note'] == current_note and
               melody_notes[j]['start'] - end_time < 0.2):
            end_time = melody_notes[j]['start'] + chunk_duration
            j += 1

        duration = end_time - start_time

        # Only keep notes that are long enough to be musically significant
        if duration >= beat_duration * 0.5:  # At least half a beat
            grouped_notes.append({
                'start': start_time,
                'end': end_time,
                'note': current_note,
                'duration': duration
            })

        i = j

    print(f"🎵 Grouped into {len(grouped_notes)} musical notes")

    # Quantize to musical durations
    print("⏱️ Quantizing to musical note values...")

    # Standard durations: quarter, half, dotted half, whole
    standard_beats = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0]

    def quantize_duration(dur):
        beats = dur / beat_duration
        closest = min(standard_beats, key=lambda x: abs(x - beats))
        return closest * beat_duration

    def quantize_start(start):
        # Snap to quarter note grid
        grid = beat_duration / 2  # Eighth note grid for more precision
        return round(start / grid) * grid

    final_notes = []
    for note in grouped_notes:
        quant_start = quantize_start(note['start'])
        quant_duration = quantize_duration(note['duration'])

        final_notes.append({
            'start': quant_start,
            'end': quant_start + quant_duration,
            'note': note['note'],
            'duration_beats': quant_duration / beat_duration
        })

    # Remove overlaps and extend notes to fill gaps for legato
    print("✂️ Removing overlaps and filling gaps for legato...")
    clean_notes = []
    for i, note in enumerate(final_notes):
        # Extend previous note to start of current note if same pitch
        if clean_notes and note['start'] > clean_notes[-1]['end']:
            # If gap is small and same pitch, extend previous note
            if note['note'] == clean_notes[-1]['note'] and note['start'] - clean_notes[-1]['end'] < 0.2:
                clean_notes[-1]['end'] = note['start']
                clean_notes[-1]['duration_beats'] = (clean_notes[-1]['end'] - clean_notes[-1]['start']) / beat_duration

        if clean_notes and note['start'] < clean_notes[-1]['end']:
            # Shorten previous note
            clean_notes[-1]['end'] = note['start']
            clean_notes[-1]['duration_beats'] = (clean_notes[-1]['end'] - clean_notes[-1]['start']) / beat_duration

        if note['end'] > note['start']:  # Valid duration
            clean_notes.append(note)

    print(f"🎉 Before simplification: {len(clean_notes)} notes")

    # SIMPLIFY BUSY SECTIONS
    print("🎯 Simplifying unplayable sections...")
    simplified_notes = simplify_busy_sections(clean_notes, beat_duration)

    print(f"✨ After simplification: {len(simplified_notes)} notes")

    # Smooth melody flow (final pass)
    print("🎶 Smoothing melody flow (final pass)...")
    simplified_notes = smooth_melody_flow(simplified_notes, min_duration=0.5, join_gap=0.25)

    # Show the melody
    if simplified_notes:
        print("\n🎼 Final playable melody:")
        for i, note in enumerate(simplified_notes):
            note_name = librosa.midi_to_note(note['note'])
            beats = note['duration_beats']
            duration_name = {
                0.5: "8th", 1.0: "quarter", 1.5: "dotted quarter",
                2.0: "half", 3.0: "dotted half", 4.0: "whole"
            }.get(beats, f"{beats:.1f} beats")

            print(f"  {i+1:2d}: {note_name:>3} ({duration_name:>12}) at {note['start']:>5.1f}s")

    return simplified_notes

def simplify_busy_sections(notes, beat_duration):
    """
    Find sections with too many notes and simplify them while keeping the musical essence
    """
    
    if not notes:
        return notes
    
    # Analyze note density - find sections with too many notes
    simplified = []
    
    # Look for busy sections (more than 4 notes per beat)
    max_notes_per_beat = 4
    analysis_window = beat_duration * 2  # Analyze 2-beat windows
    
    i = 0
    while i < len(notes):
        current_note = notes[i]
        window_start = current_note['start']
        window_end = window_start + analysis_window
        
        # Find all notes in this window
        window_notes = []
        j = i
        while j < len(notes) and notes[j]['start'] < window_end:
            window_notes.append(notes[j])
            j += 1
        
        # Check if this section is too busy
        if len(window_notes) > max_notes_per_beat * 2:  # More than 4 notes per beat * 2 beats
            print(f"  🚨 Busy section at {window_start:.1f}s: {len(window_notes)} notes in {analysis_window:.1f}s")
            
            # Simplify this section
            simplified_section = simplify_section(window_notes, beat_duration)
            simplified.extend(simplified_section)
            
            # Skip past all the notes we just processed
            i = j
        else:
            # Keep this note as-is
            simplified.append(current_note)
            i += 1
    
    return simplified

def simplify_section(busy_notes, beat_duration):
    """
    Simplify a busy section by keeping only the most important notes
    """
    
    if len(busy_notes) <= 4:
        return busy_notes
    
    print(f"    🔧 Simplifying {len(busy_notes)} notes...")
    
    # Strategy 1: Keep notes on strong beats
    strong_beat_notes = []
    for note in busy_notes:
        # Check if this note starts on or near a beat
        beats_from_start = note['start'] / beat_duration
        distance_from_beat = abs(beats_from_start - round(beats_from_start))
        
        if distance_from_beat < 0.25:  # Within 1/4 beat of a strong beat
            strong_beat_notes.append(note)
    
    # Strategy 2: If still too many, keep the longest notes
    if len(strong_beat_notes) > 6:
        strong_beat_notes.sort(key=lambda x: x['duration_beats'], reverse=True)
        strong_beat_notes = strong_beat_notes[:6]
    
    # Strategy 3: If too few, add some important off-beat notes
    if len(strong_beat_notes) < 3:
        # Sort all notes by duration and take the longest ones
        busy_notes.sort(key=lambda x: x['duration_beats'], reverse=True)
        strong_beat_notes = busy_notes[:4]
    
    # Strategy 4: Extend durations to fill gaps and make it more playable
    if len(strong_beat_notes) > 0:
        # Sort by start time
        strong_beat_notes.sort(key=lambda x: x['start'])
        
        # Extend durations to be more reasonable
        for i, note in enumerate(strong_beat_notes):
            # Minimum duration: quarter note
            if note['duration_beats'] < 1.0:
                note['duration_beats'] = 1.0
                note['end'] = note['start'] + beat_duration
            
            # Don't overlap with next note
            if i < len(strong_beat_notes) - 1:
                next_start = strong_beat_notes[i + 1]['start']
                if note['end'] > next_start:
                    note['end'] = next_start
                    note['duration_beats'] = (note['end'] - note['start']) / beat_duration
    
    print(f"    ✅ Simplified to {len(strong_beat_notes)} playable notes")
    return strong_beat_notes

def smooth_melody_flow(notes, min_duration=0.25, join_gap=0.15):
    """
    Merge short notes and join consecutive notes of the same pitch for smoother flow.
    """
    if not notes:
        return notes

    smoothed = []
    i = 0
    while i < len(notes):
        current = notes[i]
        # Merge with next note if same pitch and close in time
        j = i + 1
        while (j < len(notes) and
               notes[j]['note'] == current['note'] and
               notes[j]['start'] - current['end'] < join_gap):
            # Extend current note
            current['end'] = notes[j]['end']
            current['duration_beats'] = (current['end'] - current['start']) / (60 / 148)
            j += 1
        # Remove very short notes
        if current['duration_beats'] >= min_duration:
            smoothed.append(current)
        i = j
    return smoothed

def create_simple_midi(notes, tempo_bpm=47):
    """Create a simple MIDI file"""
    
    if not notes:
        return None
    
    print(f"\n🎹 Creating MIDI at {tempo_bpm} BPM...")
    
    midi_file = MidiFile(ticks_per_beat=480)
    track = MidiTrack()
    midi_file.tracks.append(track)
    
    # Add tempo
    tempo = bpm2tempo(tempo_bpm)
    track.append(MetaMessage("set_tempo", tempo=tempo, time=0))
    track.append(MetaMessage("track_name", name="Main Melody", time=0))
    
    # Add notes
    beat_duration = 60 / tempo_bpm
    current_tick = 0
    
    for note in notes:
        start_tick = int((note['start'] / beat_duration) * 480)
        duration_ticks = int(note['duration_beats'] * 480)
        
        time_delta = max(0, start_tick - current_tick)
        
        track.append(Message("note_on", note=note['note'], velocity=80, time=time_delta))
        track.append(Message("note_off", note=note['note'], velocity=0, time=duration_ticks))
        
        current_tick = start_tick + duration_ticks
    
    # Save MIDI
    midi_path = "main_melody.mid"
    midi_file.save(midi_path)
    print(f"✅ MIDI saved: {midi_path}")
    
    return midi_path

def create_musicxml_from_midi(midi_path):
    """Convert MIDI to MusicXML sheet music"""
    
    if not PARTITURA_AVAILABLE:
        print("❌ partitura not installed - cannot create MusicXML")
        print("💡 Install with: pip install partitura")
        return None
    
    try:
        print("📄 Converting MIDI to MusicXML...")
        score = partitura.load_score(midi_path)
        xml_path = "main_melody.musicxml"
        exportmusicxml.save_musicxml(score, xml_path)
        print(f"✅ MusicXML saved: {xml_path}")
        return xml_path
    except Exception as e:
        print(f"⚠️ MusicXML conversion failed: {e}")
        print("But you can still import the MIDI file into notation software!")
        return None

def main():
    """Extract the main melody line only"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    vocals_path = filedialog.askopenfilename(
        title="Select vocals audio file",
        filetypes=[("Audio files", "*.wav *.mp3 *.flac *.m4a"), ("All files", "*.*")]
    )
    if not vocals_path:
        print("❌ No file selected!")
        return

    tempo_bpm = 148

    # Extract main melody
    notes = extract_main_melody_line(vocals_path, tempo_bpm)

    if not notes:
        print("❌ Could not extract main melody!")
        return

    # Save data
    with open("main_melody.json", "w") as f:
        json.dump({
            "tempo_bpm": tempo_bpm,
            "note_count": len(notes),
            "notes": notes
        }, f, indent=2)

    # Create MIDI
    midi_file = create_simple_midi(notes, tempo_bpm)

    # Create MusicXML
    xml_file = None
    if midi_file:
        xml_file = create_musicxml_from_midi(midi_file)

    print(f"\n🎉 MAIN MELODY EXTRACTED!")
    print(f"📊 {len(notes)} main melody notes")
    print("📁 Files:")
    print("  - main_melody.json")
    print(f"  - {midi_file}")
    if xml_file:
        print(f"  - {xml_file}")
        print(f"\n🎼 Ready to open {xml_file} in MuseScore, Finale, or Sibelius!")
    else:
        print(f"\n🎼 You can import {midi_file} into any notation software!")
    print(f"🎯 This should sound much more like the actual song!")

if __name__ == "__main__":
    main()