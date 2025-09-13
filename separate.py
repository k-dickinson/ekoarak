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
        self.root.geometry("500x300")
        
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
        
        select_btn = tk.Button(file_frame, text="Choose MP3 File", command=self.select_file, 
                              font=("Arial", 12), bg="lightblue")
        select_btn.pack(pady=5)
        
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
            title="Select MP3 file",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )
        
        if file_path:
            self.selected_file = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"Selected: {filename}")
            self.separate_btn.config(state="normal")
            self.progress_var.set("Ready to separate audio!")
    
    def start_separation(self):
        """Start separation in a separate thread"""
        if not self.selected_file:
            messagebox.showerror("Error", "Please select an MP3 file first!")
            return
            
        # Disable button and start progress
        self.separate_btn.config(state="disabled")
        self.progress_bar.start()
        
        # Run separation in background thread
        thread = threading.Thread(target=self.separate_audio)
        thread.daemon = True
        thread.start()
        
    def separate_audio(self):
        try:
            # Import the library
            from audio_separator.separator import Separator
            
            # Create separator instance
            self.root.after(0, lambda: self.progress_var.set("Creating separator..."))
            separator = Separator()
            
            # Load default model
            self.root.after(0, lambda: self.progress_var.set("Loading AI model..."))
            separator.load_model()
            
            # Separate audio
            self.root.after(0, lambda: self.progress_var.set("Separating audio... (this may take several minutes)"))
            input_path = str(self.selected_file)
            output_files = separator.separate(input_path)
            
            # Find vocals and instrumental files
            vocals_file = None
            instrumental_file = None
            
            for file_path in output_files:
                file_path = Path(file_path)
                if 'Vocals' in file_path.name or 'vocals' in file_path.name:
                    vocals_file = file_path
                elif 'Instrumental' in file_path.name or 'instrumental' in file_path.name:
                    instrumental_file = file_path
            
            # Update UI on main thread
            self.root.after(0, self.separation_complete, vocals_file, instrumental_file)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, self.separation_error, error_msg)
    
    def separation_complete(self, vocals_file, instrumental_file):
        """Called when separation is complete"""
        self.progress_bar.stop()
        self.progress_var.set("Separation complete!")
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # Show results
        results_label = tk.Label(self.results_frame, text="Files created:", font=("Arial", 12, "bold"))
        results_label.pack()
        
        if vocals_file and vocals_file.exists():
            vocals_label = tk.Label(self.results_frame, text=f"Vocals: {vocals_file.name}", 
                                   font=("Arial", 10), fg="blue")
            vocals_label.pack(anchor="w")
            
        if instrumental_file and instrumental_file.exists():
            instrumental_label = tk.Label(self.results_frame, text=f"Instrumental: {instrumental_file.name}", 
                                         font=("Arial", 10), fg="blue")
            instrumental_label.pack(anchor="w")
        
        # Open folder button
        if vocals_file:
            folder_btn = tk.Button(self.results_frame, text="Open Output Folder", 
                                  command=lambda: self.open_folder(vocals_file.parent))
            folder_btn.pack(pady=10)
        
        # Re-enable button
        self.separate_btn.config(state="normal")
        
        messagebox.showinfo("Success", "Audio separation complete!")
    
    def separation_error(self, error_msg):
        """Called when separation fails"""
        self.progress_bar.stop()
        self.progress_var.set("Error occurred during separation")
        self.separate_btn.config(state="normal")
        messagebox.showerror("Error", f"Separation failed: {error_msg}")
    
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