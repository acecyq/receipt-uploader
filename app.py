import os
import threading
from tkinter import filedialog

import customtkinter as ctk
from dotenv import load_dotenv

from pdf_ai import pdf_info


# Load environment variables just like main.py
load_dotenv()

# Set up the visual look and feel
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ReceiptUploaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Receipt Processor & Workspace Syncer")
        self.geometry("650x750")

        self.selected_file_path = None
        self.receipt_data = None

        # --- UI LAYOUT STRUCTURE ---
        self.title_label = ctk.CTkLabel(
            self,
            text="📊 Receipt Automation Hub",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(pady=20)

        # 1. Select Receipt Button
        self.select_btn = ctk.CTkButton(self, text="📁 Choose Receipt PDF", command=self.browse_file, height=40)
        self.select_btn.pack(pady=10)

        self.file_label = ctk.CTkLabel(self, text="No file selected", font=ctk.CTkFont(slant="italic"))
        self.file_label.pack(pady=5)

        # Status Logger
        self.status_label = ctk.CTkLabel(self, text="", text_color="#10b981", font=ctk.CTkFont(weight="bold"))
        self.status_label.pack(pady=10)

        # 2. Dynamic Review Form Panel
        self.form_frame = ctk.CTkFrame(self)
        self.fields = {}

        # 3. Submit Button
        self.submit_btn = ctk.CTkButton(
            self,
            text="🚀 Approve & Sync Workspace",
            command=self.submit_data,
            state="disabled",
            fg_color="#10b981",
            hover_color="#059669"
        )
        self.submit_btn.pack(side="bottom", pady=30)

    def browse_file(self):
        """ Opens Mac Finder window to select a receipt """
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.selected_file_path = file_path
            self.file_label.configure(text=os.path.basename(file_path), font=ctk.CTkFont(slant="roman"))
            self.status_label.configure(text="Reading PDF & running Ollama inference...", text_color="#3b82f6")

            # Run Ollama in a separate background thread
            threading.Thread(target=self.process_receipt_background, args=(file_path,), daemon=True).start()

    def process_receipt_background(self, file_path):
        """ Handles AI parsing in the background """
        try:
            # 🌟 IMPORTANT: Pass cli_mode=False so it doesn't freeze waiting for terminal input
            self.receipt_data = pdf_info(file_path, cli_mode=False)

            if self.receipt_data:
                # Build the user review form on the main thread
                self.after(0, self.build_review_form)
            else:
                self.after(
                    0,
                    lambda: self.status_label.configure(text="❌ Failed to extract data.", text_color="#ef4444")
                )
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self.status_label.configure(text=f"❌ Error: {error_msg}", text_color="#ef4444"))

    def build_review_form(self):
        """ Generates input fields dynamically based on the AI data """
        self.status_label.configure(text="✨ AI Extraction Complete! Please verify values.", text_color="#10b981")

        # Clear out old form entries if analyzing a second receipt
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        self.form_frame.pack(pady=10, fill="both", expand=True, padx=40)

        # Fields we want to expose to edit in the UI
        display_fields = ['date', 'month', 'vendor', 'description', 'category',
                          'payment_method', 'amount', 'suggested_filename']

        for idx, field_name in enumerate(display_fields):
            val = getattr(self.receipt_data, field_name)

            lbl = ctk.CTkLabel(self.form_frame, text=field_name.replace("_", " ").title(), anchor="w")
            lbl.grid(row=idx, column=0, padx=10, pady=8, sticky="w")

            entry = ctk.CTkEntry(self.form_frame, width=320)
            entry.insert(0, str(val))
            entry.grid(row=idx, column=1, padx=10, pady=8, sticky="e")

            self.fields[field_name] = entry

        self.submit_btn.configure(state="normal")

    def submit_data(self):
        """ Updates the Pydantic instance, pushes to Drive, and logs to Sheets """
        self.status_label.configure(text="Uploading to Google Drive & Syncing Sheets...", text_color="#3b82f6")
        self.submit_btn.configure(state="disabled")

        # Pull user modifications from UI inputs directly back into our object
        for field_name, entry_widget in self.fields.items():
            user_value = entry_widget.get().strip()
            if field_name == "amount":
                setattr(self.receipt_data, field_name, float(user_value))
            else:
                setattr(self.receipt_data, field_name, user_value)

        # Run Google network payloads in background thread
        threading.Thread(target=self.sync_workspace_background, daemon=True).start()

    def sync_workspace_background(self):
        try:
            # Grab all the variables you normally load in main.py
            credentials_filename = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            google_drive_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

            # 1. Upload to Drive (This returns your authenticated user_creds)
            authenticated_creds = self.receipt_data.upload_to_google_drive(
                credentials_filename,
                self.selected_file_path,
                google_drive_folder_id
            )

            # 2. Save to sheets using those same credentials
            if authenticated_creds:
                self.receipt_data.save_to_google_sheets(authenticated_creds)
                self.after(
                    0,
                    lambda: self.status_label.configure(
                        text="✅ Database and Drive Synced Flawlessly!",
                        text_color="#10b981"
                    )
                )
            else:
                self.after(
                    0,
                    lambda: self.status_label.configure(
                        text="❌ Authentication failed during Drive upload.",
                        text_color="#ef4444"
                    )
                )

        except Exception as e:
            error_msg = str(e)
            self.after(
                0,
                lambda: self.status_label.configure(
                    text=f"❌ Sync Failed: {error_msg}",
                    text_color="#ef4444"
                )
            )
        finally:
            self.after(0, lambda: self.submit_btn.configure(state="normal"))

if __name__ == "__main__":
    app = ReceiptUploaderApp()
    app.mainloop()
