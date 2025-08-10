import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from gemini_client import GeminiClient
from image_processor import ImageProcessor
from concurrent.futures import ThreadPoolExecutor

class MetadataAutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Metadata Automation")
        self.root.geometry("600x400")
        
        # GUI Setup
        self.setup_ui()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def setup_ui(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Source Folder:").grid(row=0, column=0, sticky=tk.W)
        self.folder_path = tk.StringVar()
        ttk.Entry(frame, textvariable=self.folder_path, width=50).grid(row=0, column=1)
        ttk.Button(frame, text="Browse", command=self.select_folder).grid(row=0, column=2)
        
        ttk.Button(frame, text="Process Images", command=self.process_images).grid(row=1, column=1, pady=10)
        self.process_button = frame.grid_slaves(row=1, column=1)[0]
        self.process_button.config(state=tk.DISABLED)
        
        self.progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.grid(row=2, column=0, columnspan=3, pady=10)
        
        self.status = tk.StringVar()
        self.status.set("Ready")
        ttk.Label(frame, textvariable=self.status).grid(row=3, column=0, columnspan=3)
        
        self.log = tk.Text(frame, height=10, width=70)
        self.log.grid(row=4, column=0, columnspan=3, pady=10)
        
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.process_button.config(state=tk.NORMAL)
            self.log_message(f"Selected folder: {folder}")
    
    def process_images(self):
        folder = self.folder_path.get()
        if not folder:
            messagebox.showerror("Error", "Please select a folder first")
            return
        
        self.process_button.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.status.set("Processing...")
        
        try:
            image_files = self.get_image_files(folder)
            if not image_files:
                messagebox.showinfo("Info", "No images found in selected folder")
                return
            
            self.progress['maximum'] = len(image_files)
            self.process_images_async(image_files)
            
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
            self.reset_ui()
    
    def get_image_files(self, folder):
        extensions = ('.jpg', '.jpeg', '.png')
        return [os.path.join(root, f) 
                for root, _, files in os.walk(folder) 
                for f in files 
                if f.lower().endswith(extensions)]
    
    def process_images_async(self, image_files):
        gemini = GeminiClient()
        processor = ImageProcessor()
        
        def process_single(image_path):
            try:
                self.log_message(f"Processing: {os.path.basename(image_path)}")
                metadata = gemini.generate_metadata(image_path)
                if metadata:
                    processor.add_metadata(image_path, metadata)
                    self.log_message(f"Added metadata to {os.path.basename(image_path)}")
                return True
            except Exception as e:
                self.log_message(f"Error processing {image_path}: {str(e)}")
                return False
            finally:
                self.root.after(0, self.update_progress)
        
        futures = [self.executor.submit(process_single, img) for img in image_files]
        self.executor.submit(self.monitor_futures, futures)
    
    def monitor_futures(self, futures):
        for future in futures:
            future.result()  # Wait for completion or raise exception
        self.root.after(0, self.on_processing_complete)
    
    def update_progress(self):
        self.progress['value'] += 1
        self.root.update()
    
    def on_processing_complete(self):
        messagebox.showinfo("Complete", "Finished processing images")
        self.reset_ui()
    
    def reset_ui(self):
        self.status.set("Ready")
        self.process_button.config(state=tk.NORMAL)
    
    def log_message(self, message):
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = MetadataAutomationApp(root)
    root.mainloop()