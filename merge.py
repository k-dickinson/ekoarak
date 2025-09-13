import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pydub import AudioSegment
import os

class AudioMerger:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Audio Merger")
        self.root.geometry("500x350")

        # Variables
        self.vocals_file = None
        self.instrumental_file = None
        self.progress_var = tk.StringVar(value="Select your audio files...")

        self.setup_ui()

    def setup_ui(self):
        # Title
        title = tk.Label(self.root, text="Audio Merger", font=("Arial", 16, "bold"))
        title.pack(pady=20)

        # Vocals selection
        vocals_frame = tk.Frame(self.root)
        vocals_frame.pack(pady=5)
        self.vocals_label = tk.Label(vocals_frame, text="No vocals file selected", width=50, bg="lightgray", relief="sunken")
        self.vocals_label.pack(side="left", padx=5)
        vocals_btn = tk.Button(vocals_frame, text="Choose Vocals", command=self.select_vocals, bg="lightblue")
        vocals_btn.pack(side="left", padx=5)

        # Instrumental selection
        inst_frame = tk.Frame(self.root)
        inst_frame.pack(pady=5)
        self.inst_label = tk.Label(inst_frame, text="No instrumental file selected", width=50, bg="lightgray", relief="sunken")
        self.inst_label.pack(side="left", padx=5)
        inst_btn = tk.Button(inst_frame, text="Choose Instrumental", command=self.select_instrumental, bg="lightblue")
        inst_btn.pack(side="left", padx=5)

        # Merge button
        self.merge_btn = tk.Button(self.root, text="Merge Audio", command=self.merge_audio,
                                   font=("Arial", 12), bg="lightgreen", state="disabled")
        self.merge_btn.pack(pady=20)

        # Progress label
        progress_label = tk.Label(self.root, textvariable=self.progress_var, font=("Arial", 10))
        progress_label.pack(pady=10)

        # Progress bar
        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress_bar.pack(pady=5, padx=50, fill="x")

    def select_vocals(self):
        file_path = filedialog.askopenfilename(
            title="Select Vocals file",
            filetypes=[("Audio files", "*.wav *.mp3"), ("All files", "*.*")]
        )
        if file_path:
            self.vocals_file = file_path
            self.vocals_label.config(text=f"Vocals: {os.path.basename(file_path)}")
            self.check_ready()

    def select_instrumental(self):
        file_path = filedialog.askopenfilename(
            title="Select Instrumental file",
            filetypes=[("Audio files", "*.wav *.mp3"), ("All files", "*.*")]
        )
        if file_path:
            self.instrumental_file = file_path
            self.inst_label.config(text=f"Instrumental: {os.path.basename(file_path)}")
            self.check_ready()

    def check_ready(self):
        if self.vocals_file and self.instrumental_file:
            self.merge_btn.config(state="normal")

    def merge_audio(self):
        if not self.vocals_file or not self.instrumental_file:
            messagebox.showerror("Error", "Please select both vocals and instrumental files!")
            return

        try:
            self.progress_var.set("Merging audio...")
            self.progress_bar.start()

            # Load audio files
            vocals = AudioSegment.from_file(self.vocals_file)
            instrumental = AudioSegment.from_file(self.instrumental_file)

            # Match lengths
            min_len = min(len(vocals), len(instrumental))
            vocals = vocals[:min_len]
            instrumental = instrumental[:min_len]

            # Overlay
            combined = instrumental.overlay(vocals)

            # Save file
            output_path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav"), ("MP3 files", "*.mp3")],
                title="Save merged file as"
            )
            if output_path:
                combined.export(output_path, format=os.path.splitext(output_path)[1][1:])
                self.progress_var.set(f"Merge complete! Saved as {output_path}")
                messagebox.showinfo("Success", f"Audio merged and saved as:\n{output_path}")
            else:
                self.progress_var.set("Merge cancelled.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to merge audio: {str(e)}")

        finally:
            self.progress_bar.stop()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AudioMerger()
    app.run()
