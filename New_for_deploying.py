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

# === Gemini Vision Only ===
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
    file_bytes = file
    save_file_to_db("uploaded_file", file_bytes)
    byte_stream = io.BytesIO(file_bytes)

    try:
        image = Image.open(byte_stream)
        gemini_summary = gemini_understand_image(image)
        return f"""🖼️ Gemini Vision Summary:
{gemini_summary or '[No output]'}"""
    except UnidentifiedImageError:
        pages = convert_from_bytes(file_bytes, dpi=300)
        result = ""
        for i, page in enumerate(pages):
            gemini_summary = gemini_understand_image(page)
            result += f"""\n📄 Page {i+1}:
{gemini_summary or '[No output]'}\n"""
        return result.strip()
    except Exception as e:
        return f"❌ Error while processing: {str(e)}"

# === Gradio UI ===
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Gemini Vision Tool\nUpload a PDF or Image")
    with gr.Row():
        file_input = gr.File(label="Upload File", type="binary")
        output = gr.Textbox(label="Gemini Output", lines=30)
    btn = gr.Button("Analyze")

    btn.click(fn=process_file, inputs=file_input, outputs=output)

demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
