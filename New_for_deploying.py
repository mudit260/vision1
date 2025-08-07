import gradio as gr
from PIL import Image, UnidentifiedImageError
from pdf2image import convert_from_bytes
import google.generativeai as genai
import io
import os
import psycopg2
from datetime import datetime

# === Configure Gemini ===
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
vision_model = genai.GenerativeModel("gemini-1.5-flash")

# === PostgreSQL Connection ===
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def save_file_to_db(filename, content_bytes):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                id SERIAL PRIMARY KEY,
                filename TEXT,
                uploaded_at TIMESTAMP,
                file_data BYTEA
            )
        """)
        cur.execute("""
            INSERT INTO uploads (filename, uploaded_at, file_data)
            VALUES (%s, %s, %s)
        """, (filename, datetime.utcnow(), psycopg2.Binary(content_bytes)))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("❌ DB Error:", e)

# === Gemini Vision OCR Only ===
def gemini_extract_text(image):
    try:
        response = vision_model.generate_content([
            "Extract the raw text (OCR) from this image exactly as it appears. Do not summarize or interpret it.",
            image
        ])
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Gemini Vision Error: {e}"

# === File Processing ===
def process_file(file_path):
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        filename = os.path.basename(file_path)  # Extract actual filename

        save_file_to_db(filename, file_bytes)

        byte_stream = io.BytesIO(file_bytes)

        try:
            image = Image.open(byte_stream)
            gemini_text = gemini_extract_text(image)
            return f"""🖼️ Gemini OCR Text:
{gemini_text or '[No text extracted]'}"""
        except UnidentifiedImageError:
            # If not an image, treat as PDF
            pages = convert_from_bytes(file_bytes, dpi=300)
            result = ""
            for i, page in enumerate(pages):
                gemini_text = gemini_extract_text(page)
                result += f"""\n📄 Page {i+1} OCR:
{gemini_text or '[No text extracted]'}\n"""
            return result.strip()
    except Exception as e:
        return f"❌ Error: {e}"

# === Gradio UI ===
with gr.Blocks() as demo:
    gr.Markdown("## 🧾 Gemini OCR Tool\nUpload a PDF or Image to extract raw text")
    with gr.Row():
        file_input = gr.File(label="Upload File", type="file")  # ✅ changed to 'file'
        output = gr.Textbox(label="OCR Output", lines=30)
    btn = gr.Button("Extract OCR Text")

    btn.click(fn=process_file, inputs=file_input, outputs=output)

demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))

