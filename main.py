import os
import shutil
import threading
import time
from datetime import datetime
import csv
import json
import pygame
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import webbrowser
import sqlite3

from classifier import process_document, get_summary, save_document_info

#  Initialize pygame mixer
pygame.mixer.init()
# Load the sound
beep_sound = pygame.mixer.Sound('beep.wav')  # Path to your sound file

CONFIG_PATH = "config.json"
# Load existing categories from config.json
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as file:
        config = json.load(file)
else:
    config = {"categories": []}

# Access the categories array
categories = config.get("categories", [])

# Set the global theme to 'dark' which is typically the black theme
ctk.set_appearance_mode("dark")  # Options are "light", "dark", or "system"
# Optionally, set a specific color theme if needed
ctk.set_default_color_theme("blue")  # You can choose other themes as per your preference



input_folder = 'Input'
output_folder_base = 'Output'
uncategorized_folder = 'Uncategorized'

def extract_text_from_pdf(file_path):
    with fitz.open(file_path) as doc:
        page = doc[0]  # Get the first page
        text = page.get_text()
    return text

def ocr_image_from_pdf(file_path):
    with fitz.open(file_path) as doc:
        page = doc[0]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return pytesseract.image_to_string(img)

def process_file(file_path):
    text = extract_text_from_pdf(file_path)
    if not text.strip():  # If no text, use OCR
        text = ocr_image_from_pdf(file_path)

    category = process_document(os.path.basename(file_path), text)
    # print(output_folder_base, category, uncategorized_folder, os.path.basename(file_path))
    destination_folder = os.path.join(output_folder_base, category if category != "Uncategorized" else uncategorized_folder, os.path.basename(file_path))
    try:
      os.makedirs(os.path.dirname(destination_folder), exist_ok=True)
    except:
      os.makedirs(os.path.dirname(os.path.join(output_folder_base, uncategorized_folder)), exist_ok=True)
      
    shutil.move(file_path, destination_folder)
    return f"Processed and moved: {os.path.basename(file_path)} to {category}", category

class FolderMonitor(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_created(self, event):
        if not event.is_directory:
            self.app.update_log(f"File {os.path.basename(event.src_path)} is added.", "DEBUG")
            # Start a new thread for processing the file
            # threading.Thread(target=self.handle_file, args=(event.src_path,)).start()
            time.sleep(5)  # Simulate delay
            result, category = process_file(event.src_path)
            if category == "Uncategorized":
                beep_sound.play()
                self.app.update_log(f"⚠️⚠️⚠️ {result} ⚠️⚠️⚠️", "ERROR")
            else:
                self.app.update_log(f"✔️ {result}", "INFO")

    def handle_file(self, file_path):
        time.sleep(1)  # Simulate delay
        result, category = process_file(file_path)
        if category == "Uncategorized":
            beep_sound.play()
            self.app.update_log(f"⚠️⚠️⚠️ {result} ⚠️⚠️⚠️", "ERROR")
        else:
            self.app.update_log(f"✔️ {result}", "INFO")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Setup directories
        global input_folder, output_folder_base, uncategorized_folder
        
        self.title("PDF Organization Software")
        self.geometry("1200x700")

        # Create two horizontal frames
        self.left_frame = ctk.CTkFrame(self, width=700)
        self.left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        self.right_frame = ctk.CTkFrame(self, width=200)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        # Dashboard UI
        self.log = tk.Text(self.left_frame, height=10)
        self.log.pack(side='top', fill='both', expand=True, padx=5, pady=5)
        
        # Configure tags for different categories just once
        self.log.tag_configure('INFO', foreground='green')
        self.log.tag_configure('WARNING', foreground='orange')
        self.log.tag_configure('ERROR', foreground='red')
        self.log.tag_configure('DEBUG', foreground='black')
        
        # Settings UI
        # Entry for the input folder path
        self.input_folder_entry = ctk.CTkEntry(self.right_frame, placeholder_text=f"{os.path.join(os.getcwd(), input_folder)}")
        self.input_folder_entry.pack(fill='x', padx=5, pady=5)
        self.input_folder_entry.configure(state="disabled")
        # Button to browse for input folder
        self.browse_input_button = ctk.CTkButton(self.right_frame, text="Browse Central Input Folder", command=self.browse_input_folder)
        self.browse_input_button.pack(fill='x', padx=5, pady=5)
        
        
        
        self.learning_mode = ctk.CTkSwitch(self.right_frame, text="Learning Mode")
        self.learning_mode.pack(padx=5, pady=5)

        self.search_entry = ctk.CTkEntry(self.right_frame, placeholder_text="Search files...")
        self.search_entry.pack(fill='x', padx=5, pady=5)
        self.search_button = ctk.CTkButton(self.right_frame, text="Search", command=self.perform_search)
        self.search_button.pack(fill='x', padx=5, pady=5)
         # Change to using Listbox for search results
        self.search_results = tk.Listbox(self.right_frame, height=15)
        self.search_results.pack(fill='x', pady=5)

        self.open_file_button = ctk.CTkButton(self.right_frame, text="Open Selected File", command=self.open_selected_file)
        self.open_file_button.pack(fill='x', pady=5)
        
        # self.left_frame = ctk.CTkFrame(self)
        # self.left_frame.pack(pady=10)

        self.start_button = ctk.CTkButton(self.left_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(side='left', padx=10)

        self.manual_button = ctk.CTkButton(self.left_frame, text="Manual Classify", command=self.open_manual_classify)
        self.manual_button.pack(side='right', padx=10)
        

    def update_log(self, message, msg_type = "orange"):
        self.log.insert(tk.END, message + "\n", msg_type)
        self.log.yview(tk.END)
         # Generate current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        csv_file = 'log_trace.csv'
        csv_headers = ['Timestamp', 'Message', 'Message_Type']
        
        # Initialize the CSV file with headers if it doesn't exist
        if not os.path.isfile(csv_file):
            with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(csv_headers)
        
        # Append the log entry to the CSV file
        try:
            with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, message, msg_type])
        except Exception as e:
            # Handle exceptions (e.g., file write errors)
            error_message = f"Failed to write log to CSV: {e}"
            self.log.insert(tk.END, error_message + "\n", "red")
            self.log.yview(tk.END)

    def browse_input_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.input_folder_entry.configure(state="normal")
            self.input_folder_entry.delete(0, "end")
            self.input_folder_entry.insert(0, folder_selected)

            # Disable the entry and browse button to lock the setting
            self.input_folder_entry.configure(state="disabled")
            input_folder = folder_selected
            # self.browse_input_button.configure(state="disabled")
            # self.lock_button.configure(state="disabled")

    def open_selected_file(self):
      # Ask the user to select a file
      filename = filedialog.askopenfilename(initialdir=output_folder_base, title="Select file", filetypes=[("PDF files", "*.pdf")])
      # Check if a file was selected
      if filename:
          # Open the file with the default application associated with PDF files on the user's system
          webbrowser.open(filename)
                 
                       
    def perform_search(self):
        search_query = self.search_entry.get().lower()
        connection = sqlite3.connect('documents.db')
        cursor = connection.cursor()
        # Fetch data from database where any of filename, category, or summary contains the search query
        query = '''
            SELECT filename, category, summary 
            FROM documents 
            WHERE filename LIKE ? OR category LIKE ? OR summary LIKE ?
        '''
        pattern = '%' + search_query + '%'
        cursor.execute(query, (pattern, pattern, pattern))
        found_files = cursor.fetchall()

        self.search_results.delete(0, tk.END)  # Clear previous search results
        if found_files:
            for filename, category, summary in found_files:
                # Format the result as "Category -> Filename: Summary"
                result = f"{category} -> {filename}"
                # result = f"{category} -> {filename}: {summary}"
                self.search_results.insert(tk.END, result)  # Add files to the listbox
        else:
            self.search_results.insert(tk.END, "No documents found.")

    def open_selected_file(self):
        try:
            selected_index = self.search_results.curselection()[0]  # Get index of the selected item
            selected_file = self.search_results.get(selected_index)  # Get the file path from the listbox
            folder = selected_file.split(" -> ")[0]
            file = selected_file.split(" -> ")[1]
            file_path = folder + "\\" + file
            file_path = os.path.join(output_folder_base, file_path)
            
            webbrowser.open(file_path)  # Open the file with the default PDF viewer or web browser
        except IndexError:
            print("No file selected")

    def start_monitoring(self):
        observer = Observer()
        event_handler = FolderMonitor(self)
        observer.schedule(event_handler, input_folder, recursive=False)
        observer.start()
        self.start_button.configure(state='disabled')
        self.update_log(f"🔎 Monitoring...", "WARNING")
        
        threading.Thread(target=observer.join).start()

    def open_manual_classify(self):
        # Open a new window to handle manual classification
        manual_window = ctk.CTkToplevel(self)
        manual_window.title("Manual Classification")
        manual_window.geometry("600x400")
        # Create two horizontal frames
        left_frame = ctk.CTkFrame(manual_window)
        left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        right_frame = ctk.CTkFrame(manual_window)
        right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        # Set this window as the topmost window with modal effects
        manual_window.grab_set()
        # Make sure the window stays on top of its parent window
        manual_window.transient(self)
        destination_folder = os.path.join(output_folder_base, uncategorized_folder)
        # Ensure the destination folder exists
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)  # Create the directory because it doesn't exist
        # Fetch list of unclassified documents
        unclassified_files = os.listdir(destination_folder)
        # if not unclassified_files:
        #     ctk.CTkLabel(left_frame, text="No documents to classify").pack(fill='x', padx=5, pady=5)
        #     return
        
            
        # Dropdown for selecting the document
        file_var = ctk.StringVar(left_frame)
        if(len(unclassified_files) != 0):
            file_var.set(unclassified_files[0])
        else:
            file_var.set('No unclassified files')
        file_dropdown = ctk.CTkOptionMenu(left_frame, variable=file_var, values=unclassified_files)
        file_dropdown.pack(fill='x', padx=5, pady=5)

        # Function to open the selected file.
        def open_file():
            selected_file = file_var.get()
            selected_category = category_var.get()
            src_path = os.path.join(destination_folder, selected_file)
            webbrowser.open(src_path)
            
        open_file_button = ctk.CTkButton(left_frame, text="Open File", command=open_file)
        open_file_button.pack(fill='x', padx=5, pady=5)

        category_var = ctk.StringVar(left_frame)
        category_var.set("Uncategorized")
        category_options = categories  # Add more categories as required
        category_dropdown = ctk.CTkOptionMenu(left_frame, variable=category_var, values=category_options)
        category_dropdown.pack(fill='x', padx=5, pady=5)

        # Function to handle saving the classification
        def save_classification():
            selected_file = file_var.get()
            selected_category = category_var.get()
            src_path = os.path.join(destination_folder, selected_file)
            dst_path = os.path.join(output_folder_base, selected_category, selected_file)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            
            
            text = extract_text_from_pdf(src_path)
            if not text.strip():  # If no text, use OCR
                text = ocr_image_from_pdf(src_path)
            summary = get_summary(text)
            save_document_info(selected_file, selected_category, summary)
            
            shutil.move(src_path, dst_path)
            self.update_log(f"Manually classified and moved: {selected_file} to {selected_category}", "INFO")
            #   manual_window.destroy()

        # Save Button
        save_button = ctk.CTkButton(left_frame, text="Save Classification", command=save_classification)
        save_button.pack(fill='x', padx=5, pady=5)
        
        # Configure the parent frame to allow column resizing
        right_frame.grid_columnconfigure(0, weight=1)  # Make column 0 resizable
        right_frame.grid_columnconfigure(1, weight=1)  # Make column 1 resizable
        
        # Add Label
        add_label = ctk.CTkLabel(right_frame, text="Add Custom Category")
        add_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Category Entry
        category_entry = ctk.CTkEntry(right_frame, placeholder_text="Custom Category")
        category_entry.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Function to save the custom category
        def add_custom():
            category = category_entry.get()
            if category and category not in config["categories"]:
                config["categories"].append(category)
                with open(CONFIG_PATH, "ew") as file:
                    json.dump(config, file, indent=4)
                # Update the dropdown with new values
                category_dropdown.configure(values=config["categories"])
                category_var.set(category)  # Optionally set the new category as selected
                messagebox.showinfo("Success", f"Category '{category}' added successfully!")
            elif not category:
                messagebox.showwarning("Warning", "Category name cannot be empty!")
            else:
                messagebox.showerror("Error", f"Category '{category}' already exists.")

        # Add Button
        add_button = ctk.CTkButton(right_frame, text="Add Category", command=add_custom)
        add_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Edit Label
        edit_label = ctk.CTkLabel(right_frame, text="Update/Delete Category")
        edit_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Categories Dropdown
        categories_var = ctk.StringVar(right_frame)
        categories_var.set("Uncategorized")
        categories_dropdown = ctk.CTkOptionMenu(right_frame, variable=categories_var, values=config["categories"])
        categories_dropdown.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Update Entry
        update_entry = ctk.CTkEntry(right_frame, placeholder_text="Uncategorized")
        update_entry.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Function to populate the update entry with selected category
        def populate_update_entry(*args):
            selected_category = categories_var.get()
            update_entry.delete(0, 'end')
            update_entry.insert(0, selected_category)

        categories_var.trace_add("write", populate_update_entry)

        # Function to update the selected category
        def update_category():
            selected_category = categories_var.get()
            updated_category = update_entry.get()
            
            if not updated_category:
                messagebox.showwarning("Warning", "Updated category name cannot be empty!")
                return
            
            if selected_category in config["categories"]:
                index = config["categories"].index(selected_category)
                config["categories"][index] = updated_category
                
                with open(CONFIG_PATH, "w") as file:
                    json.dump(config, file, indent=4)
                
                # Update dropdown with new values
                categories_dropdown.configure(values=config["categories"])
                categories_var.set(updated_category)  # Set updated category as selected
                messagebox.showinfo("Success", f"Category '{selected_category}' updated to '{updated_category}' successfully!")
            else:
                messagebox.showerror("Error", f"Category '{selected_category}' not found.")

        # Update Button
        update_button = ctk.CTkButton(right_frame, text="Update", command=update_category)
        update_button.grid(row=6, column=0, columnspan=1, padx=5, pady=5, sticky="ew")

        # Function to delete the selected category
        def delete_category():
            selected_category = categories_var.get()
            
            if selected_category in config["categories"]:
                config["categories"].remove(selected_category)
                
                with open(CONFIG_PATH, "w") as file:
                    json.dump(config, file, indent=4)
                
                # Update dropdown with new values
                categories_dropdown.configure(values=config["categories"])
                categories_var.set("Uncategorized")  # Reset selection
                update_entry.delete(0, 'end')  # Clear the entry field
                messagebox.showinfo("Success", f"Category '{selected_category}' deleted successfully!")
            else:
                messagebox.showerror("Error", f"Category '{selected_category}' not found.")

        # Delete Button
        delete_button = ctk.CTkButton(right_frame, text="Delete", command=delete_category)
        delete_button.grid(row=6, column=1, columnspan=1, padx=5, pady=5, sticky="ew")


if __name__ == "__main__":
    app = App()
    app.mainloop()
