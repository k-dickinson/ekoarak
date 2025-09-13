import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import sys
import os
from pathlib import Path
import threading

class AudioSeparator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Audio Separator")
        self.root.geometry("500x350")
        
        # Variables
        self.selected_file = None
        self.progress_var = tk.StringVar(value="Ready to select file...")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title = tk.Label(self.root, text="Audio Separator", font=("Arial", 16, "bold"))
        title.pack(pady=20)
        
        # File selection
        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=10)
        
        self.file_label = tk.Label(file_frame, text="No file selected", width=50, bg="lightgray", relief="sunken")
        self.file_label.pack(pady=5)
        
        select_btn = tk.Button(file_frame, text="Choose Audio File", command=self.select_file, 
                              font=("Arial", 12), bg="lightblue")
        select_btn.pack(pady=5)
        
        # Quick install button
        install_btn = tk.Button(file_frame, text="📦 Install Libraries", command=self.quick_install,
                               font=("Arial", 10), bg="yellow")
        install_btn.pack(pady=5)
        
        # Separate button
        self.separate_btn = tk.Button(self.root, text="Separate Audio", command=self.start_separation,
                                     font=("Arial", 12), bg="lightgreen", state="disabled")
        self.separate_btn.pack(pady=20)
        
        # Progress
        progress_label = tk.Label(self.root, textvariable=self.progress_var, font=("Arial", 10))
        progress_label.pack(pady=10)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress_bar.pack(pady=5, padx=50, fill="x")
        
        # Results frame
        self.results_frame = tk.Frame(self.root)
        self.results_frame.pack(pady=20)
        
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select audio file",
            filetypes=[
                ("Audio files", "*.mp3 *.wav *.flac *.m4a"),
                ("MP3 files", "*.mp3"), 
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.selected_file = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"Selected: {filename}")
            self.separate_btn.config(state="normal")
            self.progress_var.set("Ready to separate audio!")
    
    def quick_install(self):
        """Install required libraries"""
        def install():
            try:
                self.progress_var.set("Installing audio separation libraries...")
                self.progress_bar.start()
                
                # Try to install the most reliable option
                libraries = ["spleeter", "tensorflow", "librosa", "soundfile", "demucs"]
                
                for lib in libraries:
                    self.progress_var.set(f"Installing {lib}...")
                    result = subprocess.run([sys.executable, "-m", "pip", "install", lib], 
                                          capture_output=True, text=True)
                
                self.progress_bar.stop()
                self.progress_var.set("Installation complete!")
                messagebox.showinfo("Success", "Libraries installed! You can now separate audio.")
                
            except Exception as e:
                self.progress_bar.stop()
                self.progress_var.set("Installation failed")
                messagebox.showerror("Error", f"Installation failed: {str(e)}\n\nTry running:\npip install spleeter tensorflow librosa soundfile demucs")
        
        thread = threading.Thread(target=install)
        thread.daemon = True
        thread.start()
    
    def start_separation(self):
        """Start separation in a separate thread"""
        if not self.selected_file:
            messagebox.showerror("Error", "Please select an audio file first!")
            return
            
        # Disable button and start progress
        self.separate_btn.config(state="disabled")
        self.progress_bar.start()
        
        # Run separation in background thread
        thread = threading.Thread(target=self.separate_audio)
        thread.daemon = True
        thread.start()
        
    def separate_audio(self):
        """Try different separation methods - BETTER METHODS"""
        
        # Method 1: Try Demucs (BEST quality - used by professionals)
        try:
            self.separate_with_demucs()
            return
        except Exception as e:
            print(f"Demucs failed: {e}")
        
        # Method 2: Try improved Spleeter
        try:
            self.separate_with_spleeter_better()
            return
        except Exception as e:
            print(f"Spleeter failed: {e}")
        
        # If all methods fail
        self.root.after(0, self.separation_error, 
                       "Separation failed. Please install better libraries using the '📦 Install Libraries' button (this installs Demucs - much better quality).")
    
    def separate_with_demucs(self):
        """Use Demucs - PROFESSIONAL QUALITY separation"""
        self.root.after(0, lambda: self.progress_var.set("🔥 Using Demucs (professional quality)..."))
        
        # Create output directory
        base_path = Path(self.selected_file).parent
        base_name = Path(self.selected_file).stem
        output_dir = base_path / f"{base_name}_separated"
        
        # Run Demucs via command line (this is the easiest way)
        self.root.after(0, lambda: self.progress_var.set("🎵 AI is separating your audio... (this takes a few minutes but worth it!)"))
        
        result = subprocess.run([
            sys.executable, "-m", "demucs.separate", 
            "--two-stems=vocals",  # Only separate vocals and accompaniment
            "-o", str(base_path),
            str(self.selected_file)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Demucs failed: {result.stderr}")
        
        # Find the output files (Demucs creates a specific folder structure)
        demucs_output = base_path / "separated" / "htdemucs" / base_name
        
        vocals_path = None
        instrumental_path = None
        
        # Look for vocals and no_vocals files
        if demucs_output.exists():
            for file in demucs_output.glob("*.wav"):
                if "vocals" in file.name.lower():
                    vocals_path = file
                elif "no_vocals" in file.name.lower():
                    instrumental_path = file
        
        # If not found in expected location, search more broadly
        if not vocals_path:
            for file in base_path.rglob("*.wav"):
                if "vocals" in file.name.lower() and base_name in str(file):
                    vocals_path = file
                elif "no_vocals" in file.name.lower() and base_name in str(file):
                    instrumental_path = file
        
        if not vocals_path:
            raise Exception("Could not find separated vocals file")
        
        self.root.after(0, self.separation_complete, vocals_path, instrumental_path)
    
    def separate_with_spleeter_better(self):
        """Use Spleeter with better settings"""
        from spleeter.separator import Separator
        import librosa
        import soundfile as sf
        import numpy as np
        
        self.root.after(0, lambda: self.progress_var.set("🎵 Using Spleeter (improved settings)..."))
        
        # Use the higher quality 4-stem model first, then combine
        separator = Separator('spleeter:4stems-16kHz')  # vocals, drums, bass, other
        
        self.root.after(0, lambda: self.progress_var.set("🎤 Advanced separation in progress..."))
        
        # Load audio with better settings
        waveform, sample_rate = librosa.load(self.selected_file, sr=44100, mono=False)  # Higher sample rate
        
        # Ensure stereo
        if len(waveform.shape) == 1:
            waveform = np.array([waveform, waveform])
        elif waveform.shape[0] > 2:
            waveform = waveform[:2]  # Take first 2 channels
        
        waveform = waveform.T  # Shape: (time, channels)
        
        # Separate into 4 stems
        prediction = separator.separate(waveform)
        
        # Create better instrumental by combining drums + bass + other (everything except vocals)
        instrumental = prediction['drums'] + prediction['bass'] + prediction['other']
        
        # Create output files
        base_path = Path(self.selected_file).parent
        base_name = Path(self.selected_file).stem
        
        vocals_path = base_path / f"{base_name}_vocals.mp3"
        instrumental_path = base_path / f"{base_name}_instrumental.mp3"
        
        # Save with higher quality
        sf.write(str(vocals_path), prediction['vocals'], sample_rate, format='MP3')
        sf.write(str(instrumental_path), instrumental, sample_rate, format='MP3')
        
        self.root.after(0, self.separation_complete, vocals_path, instrumental_path)
    
    def separation_complete(self, vocals_file, instrumental_file):
        """Called when separation is complete"""
        self.progress_bar.stop()
        self.progress_var.set("✅ Separation complete!")
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # Show results
        results_label = tk.Label(self.results_frame, text="🎉 Files created:", font=("Arial", 12, "bold"))
        results_label.pack()
        
        if vocals_file and vocals_file.exists():
            vocals_label = tk.Label(self.results_frame, text=f"🎤 Vocals: {vocals_file.name}", 
                                   font=("Arial", 10), fg="blue")
            vocals_label.pack(anchor="w")
            
        if instrumental_file and instrumental_file.exists():
            instrumental_label = tk.Label(self.results_frame, text=f"🎵 Instrumental: {instrumental_file.name}", 
                                         font=("Arial", 10), fg="blue")
            instrumental_label.pack(anchor="w")
        
        # Open folder button
        if vocals_file:
            folder_btn = tk.Button(self.results_frame, text="📁 Open Output Folder", 
                                  command=lambda: self.open_folder(vocals_file.parent))
            folder_btn.pack(pady=10)
        
        # Re-enable button
        self.separate_btn.config(state="normal")
        
        messagebox.showinfo("Success", "🎉 Audio separation complete!")
    
    def separation_error(self, error_msg):
        """Called when separation fails"""
        self.progress_bar.stop()
        self.progress_var.set("❌ Separation failed")
        self.separate_btn.config(state="normal")
        messagebox.showerror("Error", f"❌ Separation failed:\n\n{error_msg}\n\nTry clicking '📦 Install Libraries' first!")
    
    def open_folder(self, folder_path):
        """Open the output folder"""
        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
        except:
            messagebox.showinfo("Info", f"Output folder: {folder_path}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AudioSeparator()
    app.run()