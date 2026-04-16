import customtkinter as ctk
import threading
import os
import requests
import re
from PIL import Image
from io import BytesIO
from fpdf import FPDF
from google import genai
from google.genai import types

# --- Configuration & Theme ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
BACKGROUND_COLOR = "#1e1e2e"
PANEL_COLOR = "#2a2a3c"
TEXT_COLOR = "#cdd6f4"
ACCENT_COLOR = "#89b4fa"

class EbookGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Ebook Generator Pro - Digital Products")
        self.geometry("1400x850")
        self.configure(fg_color=BACKGROUND_COLOR)
        
        # Default API Key from env if available
        self.default_api_key = os.environ.get("GEMINI_API_KEY", "")
        self.current_api_key = ""

        # Configure Layout Grid (2 Columns: Input 30%, Result 70%)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=7)
        self.grid_rowconfigure(0, weight=1)

        self._create_input_panel()
        self._create_result_panel()

        # State Variables
        self.generated_title = ""
        self.generated_description = ""
        self.generated_content = ""
        self.cover_image_path = ""

    def _create_input_panel(self):
        self.input_frame = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=15)
        self.input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        title_label = ctk.CTkLabel(self.input_frame, text="Ebook Input Configuration", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        title_label.pack(pady=(20, 30), padx=20, anchor="w")

        # API Key Input
        api_label = ctk.CTkLabel(self.input_frame, text="Gemini API Key:", font=ctk.CTkFont(size=14), text_color=TEXT_COLOR)
        api_label.pack(pady=(0, 5), padx=20, anchor="w")
        
        self.api_key_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter your Gemini API Key here...", show="*", height=35)
        self.api_key_entry.pack(pady=(0, 20), padx=20, fill="x")
        if self.default_api_key:
            self.api_key_entry.insert("0", self.default_api_key)

        # Idea Input
        idea_label = ctk.CTkLabel(self.input_frame, text="Input Idea / Topic for Ebook:", font=ctk.CTkFont(size=14), text_color=TEXT_COLOR)
        idea_label.pack(pady=(0, 5), padx=20, anchor="w")
        
        self.idea_textbox = ctk.CTkTextbox(self.input_frame, height=120, font=ctk.CTkFont(size=14))
        self.idea_textbox.pack(pady=(0, 20), padx=20, fill="x")

        # Generate Button
        self.generate_btn = ctk.CTkButton(self.input_frame, text="Generate Everything with AI", height=50, 
                                          font=ctk.CTkFont(size=16, weight="bold"), 
                                          command=self.start_generation_thread)
        self.generate_btn.pack(pady=(10, 20), padx=20, fill="x")

        # Create PDF Button (Initially Disabled)
        self.export_btn = ctk.CTkButton(self.input_frame, text="Export Ebook to PDF", height=50, 
                                        font=ctk.CTkFont(size=16, weight="bold"), 
                                        fg_color="#a6e3a1", hover_color="#94e2d5", text_color="#11111b",
                                        command=self.export_pdf, state="disabled")
        self.export_btn.pack(pady=(10, 20), padx=20, fill="x")
        
        # Status Label
        self.status_label = ctk.CTkLabel(self.input_frame, text="Ready.", font=ctk.CTkFont(size=14), text_color=TEXT_COLOR)
        self.status_label.pack(pady=(10, 10), padx=20, anchor="w")

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self.input_frame, mode="indeterminate")
        self.progress_bar.pack(pady=(0, 20), padx=20, fill="x")
        self.progress_bar.set(0)

    def _create_result_panel(self):
        self.result_frame = ctk.CTkScrollableFrame(self, fg_color=PANEL_COLOR, corner_radius=15)
        self.result_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        res_title_label = ctk.CTkLabel(self.result_frame, text="Generated Results", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        res_title_label.pack(pady=(20, 20), padx=20, anchor="w")

        # SEO Friendly Title
        title_hdr = ctk.CTkLabel(self.result_frame, text="SEO Friendly Title:", font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT_COLOR)
        title_hdr.pack(pady=(10, 5), padx=20, anchor="w")
        self.result_title = ctk.CTkEntry(self.result_frame, font=ctk.CTkFont(size=14), state="readonly")
        self.result_title.pack(pady=(0, 20), padx=20, fill="x")

        # SEO Friendly Description
        desc_hdr = ctk.CTkLabel(self.result_frame, text="SEO Friendly Product Description:", font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT_COLOR)
        desc_hdr.pack(pady=(10, 5), padx=20, anchor="w")
        self.result_desc = ctk.CTkTextbox(self.result_frame, height=180, font=ctk.CTkFont(size=14))
        self.result_desc.pack(pady=(0, 20), padx=20, fill="x")

        # Ebook Content
        content_hdr = ctk.CTkLabel(self.result_frame, text="Ebook Content (Chapters):", font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT_COLOR)
        content_hdr.pack(pady=(10, 5), padx=20, anchor="w")
        self.result_content = ctk.CTkTextbox(self.result_frame, height=300, font=ctk.CTkFont(size=14))
        self.result_content.pack(pady=(0, 20), padx=20, fill="x")
        
        # Image Display Area
        image_hdr = ctk.CTkLabel(self.result_frame, text="Generated Ebook Cover (Using Gemini Imagen):", font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT_COLOR)
        image_hdr.pack(pady=(10, 5), padx=20, anchor="w")
        
        self.image_label = ctk.CTkLabel(self.result_frame, text="No Image Generated Yet. Cover will appear here.", width=300, height=400, fg_color="#181825", corner_radius=10)
        self.image_label.pack(pady=(0, 20), padx=20)

    def start_generation_thread(self):
        idea = self.idea_textbox.get("1.0", "end-1c").strip()
        self.current_api_key = self.api_key_entry.get().strip()
        
        if not self.current_api_key:
            self.status_label.configure(text="Error: Please enter your Gemini API Key first!")
            return
            
        if not idea:
            self.status_label.configure(text="Error: Please input an idea first!")
            return

        self.generate_btn.configure(state="disabled")
        self.export_btn.configure(state="disabled")
        self.progress_bar.start()
        
        # Clear previous results
        self.result_title.configure(state="normal")
        self.result_title.delete("0", "end")
        self.result_title.configure(state="readonly")
        
        self.result_desc.delete("1.0", "end")
        self.result_content.delete("1.0", "end")
        self.image_label.configure(image=None, text="Generating image...")

        thread = threading.Thread(target=self.generate_all_content, args=(idea,))
        thread.start()

    def generate_all_content(self, idea):
        try:
            client = genai.Client(api_key=self.current_api_key)
            
            # 1. Generate SEO Title
            self.update_status(f"Generating SEO Title for '{idea[:20]}...'")
            title_prompt = f"Provide exactly one highly attractive, SEO friendly title for an ebook to be sold as a digital product. The topic is: {idea}. Only output the title string, no markdown headers or quotes."
            title_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=title_prompt
            )
            self.generated_title = title_response.text.strip().replace('"', '').replace('*', '')
            self.update_ui_text_entry(self.result_title, self.generated_title)

            # 2. Generate SEO Description
            self.update_status("Generating SEO Description...")
            desc_prompt = f"Write a persuasive, SEO-friendly product description for the digital ebook titled '{self.generated_title}'. It should convince people to buy it. Include bullet points of what they will learn. No introduction, just the copy."
            desc_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=desc_prompt
            )
            self.generated_description = desc_response.text.strip()
            self.update_ui_textbox(self.result_desc, self.generated_description)

            # 3. Generate Ebook Content
            self.update_status("Generating full Ebook Content (This might take a while)...")
            content_prompt = f"Write a comprehensive, professional ebook based on the title '{self.generated_title}'. Include an Introduction, at least 3 detailed chapters, and a Conclusion. Provide high-value information. Use Markdown formatting for headers."
            content_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=content_prompt
            )
            self.generated_content = content_response.text.strip()
            self.update_ui_textbox(self.result_content, self.generated_content)
            
            # 4. Generate Image using Gemini Imagen or fallback
            self.update_status("Generating Ebook Cover Image...")
            image_prompt = f"A professional minimalist ebook cover design for a book titled '{self.generated_title}'. High quality, modern abstract vector art, typography style, compelling colors, clean layout, no actual text rendered just the visual style."
            
            try:
                image_bytes = None
                try:
                    result = client.models.generate_images(
                        model='imagen-3.0-generate-001',
                        prompt=image_prompt,
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            output_mime_type="image/jpeg",
                            aspect_ratio="3:4" 
                        )
                    )
                    if result.generated_images:
                        image_bytes = result.generated_images[0].image.image_bytes
                except Exception as img_err:
                    print(f"Gemini Imagen failed or unavailable ({img_err}). Using alternative AI...")
                    safe_prompt = requests.utils.quote(image_prompt + " clean ebook cover no text")
                    img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=600&height=800&nologo=true"
                    resp = requests.get(img_url)
                    if resp.status_code == 200:
                        image_bytes = resp.content
                
                if image_bytes:
                    img = Image.open(BytesIO(image_bytes))
                    if not os.path.exists("outputs"):
                        os.makedirs("outputs")
                    file_name = f"outputs/cover_{self.generated_title.replace(' ', '_')[:20]}.jpg"
                    file_name = "".join([c for c in file_name if c.isalpha() or c.isdigit() or c==' ' or c=='/' or c=='.' or c=='_']).rstrip()
                    img.save(file_name)
                    self.cover_image_path = file_name
                    
                    img.thumbnail((300, 400))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    self.safe_after(lambda: self.image_label.configure(image=ctk_img, text=""))
                else:
                    self.safe_after(lambda: self.image_label.configure(text="No image returned."))
            except Exception as e:
                print(f"Image generation error: {e}")
                err_msg = str(e)[:50]
                self.safe_after(lambda err=err_msg: self.image_label.configure(text=f"Failed to generate cover image. Error: {err}"))

            self.update_status("Generation Complete!")
            self.safe_after(lambda: self.export_btn.configure(state="normal"))

        except Exception as e:
            err_msg = str(e)
            self.update_status(f"Error occurred: {err_msg}")
            print(f"Full error: {e}")
        finally:
            self.safe_after(self.progress_bar.stop)
            self.safe_after(lambda: self.generate_btn.configure(state="normal"))

    # Helper methods for updating UI safely from thread
    def safe_after(self, func):
        try:
            self.after(0, func)
        except RuntimeError:
            pass # Ignore if window is destroyed

    def update_status(self, message):
        self.safe_after(lambda: self.status_label.configure(text=message))

    def update_ui_text_entry(self, widget, text):
        def _update():
            widget.configure(state="normal")
            widget.delete("0", "end")
            widget.insert("0", text)
            widget.configure(state="readonly")
        self.safe_after(_update)
        
    def update_ui_textbox(self, widget, text):
        def _update():
            widget.delete("1.0", "end")
            widget.insert("1.0", text)
        self.safe_after(_update)

    def export_pdf(self):
        if not self.generated_content or not self.generated_title:
            self.status_label.configure(text="No content to export!")
            return

        try:
            self.status_label.configure(text="Creating PDF, please wait...")
            
            pdf = FPDF()
            
            # --- Page 1: Cover Page (Full/Large) ---
            if self.cover_image_path and os.path.exists(self.cover_image_path):
                pdf.add_page()
                COVER_WIDTH = 190
                # Posisi center kira-kira
                x_pos = (pdf.w - COVER_WIDTH) / 2
                pdf.image(self.cover_image_path, x=x_pos, y=10, w=COVER_WIDTH)
            
            # --- Page 2: Title & Copyright Info ---
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 28)
            pdf.ln(50)
            safe_title = self.generated_title.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 15, safe_title, align="C")
            
            pdf.ln(20)
            pdf.set_font('Helvetica', 'I', 16)
            pdf.cell(0, 10, "A Comprehensive Guide", new_x="LMARGIN", new_y="NEXT", align="C")
            
            pdf.ln(40)
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(0, 10, "Copyright \xa9 2026. All Rights Reserved.", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.cell(0, 5, "Generated by AI Ebook Generator Pro", new_x="LMARGIN", new_y="NEXT", align="C")
            
            # --- Page 3+: Main Content with HTML Rendering ---
            pdf.add_page()
            pdf.set_font('Helvetica', '', 12)
            
            import markdown
            # Supaya simbol tetap bisa di-print dengan aman tanpa error encoding FPDF
            clean_content = self.generated_content.encode('latin-1', 'replace').decode('latin-1')
            html_content = markdown.markdown(clean_content)
            
            pdf.write_html(html_content)
            
            if not os.path.exists("outputs"):
                os.makedirs("outputs")
            
            safe_filename = "".join([c for c in self.generated_title if c.isalpha() or c.isdigit()]).rstrip()
            if not safe_filename:
                safe_filename = "Generated_Ebook"
            output_path = f"outputs/{safe_filename}.pdf"
            
            pdf.output(output_path)
            
            self.status_label.configure(text=f"PDF exported successfully to {output_path}")
            
            # Optionally open the file specifically on Windows
            if os.name == 'nt':
                os.startfile(os.path.abspath(output_path))
                
        except Exception as e:
            self.status_label.configure(text=f"Error exporting PDF: {str(e)}")
            print(f"PDF Error: {e}")

if __name__ == "__main__":
    app = EbookGeneratorApp()
    app.mainloop()
