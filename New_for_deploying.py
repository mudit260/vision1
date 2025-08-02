import gradio as gr
from PIL import Image, UnidentifiedImageError
from pdf2image import convert_from_bytes
import pytesseract
import google.generativeai as genai
import io
import os
import psycopg2
from datetime import datetime

# === Configure Gemini ===
genai.configure(api_key=os.getenv("AIzaSyCK0zO_Sgwjf5V9Ml6NLdWs3Q0yboNWWT8"))
vision_model = genai.GenerativeModel("gemini-1.5-flash")

# === PostgreSQL Connection ===
def get_db_connection():
    return psycopg2.connect(os.getenv("postgresql://neondb_owner:npg_VJOpQKaF5b7N@ep-sweet-dew-ae7b9y9b-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"))

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

# === OCR + Gemini ===
def extract_text_from_image(image):
    return pytesseract.image_to_string(image)

def gemini_understand_image(image):
    try:
        response = vision_model.generate_content([
            "Describe or summarize the contents of this image clearly.",
            image
        ])
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Gemini Vision Error: {e}"

def process_file(file):
    file_bytes = file.read()
    save_file_to_db(file.name, file_bytes)
    byte_stream = io.BytesIO(file_bytes)

    try:
        image = Image.open(byte_stream)
        ocr_text = extract_text_from_image(image).strip()
        gemini_summary = gemini_understand_image(image)
        return f"""🖼️ Image Analysis:
🔹 OCR Text:
{ocr_text or '[No text found]'}

🔹 Gemini Vision:
{gemini_summary or '[No output]'}"""
    except UnidentifiedImageError:
        pages = convert_from_bytes(file_bytes, dpi=300)
        result = ""
        for i, page in enumerate(pages):
            ocr_text = extract_text_from_image(page).strip()
            gemini_summary = gemini_understand_image(page)
            result += f"""\n📄 Page {i+1}:
🔹 OCR Text:
{ocr_text or '[No text found]'}

🔹 Gemini Vision:
{gemini_summary or '[No output]'}\n"""
        return result.strip()
    except Exception as e:
        return f"❌ Error while processing: {str(e)}"

# === Gradio UI ===
with gr.Blocks() as demo:
    gr.Markdown("## 🔍 Gemini Vision + OCR Tool\nUpload a PDF or Image")
    with gr.Row():
        file_input = gr.File(label="Upload File", type="binary")
        output = gr.Textbox(label="Output", lines=30)
    btn = gr.Button("Analyze")

    btn.click(fn=process_file, inputs=file_input, outputs=output)

demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))



