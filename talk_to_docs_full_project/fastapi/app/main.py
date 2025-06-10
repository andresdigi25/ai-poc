from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import base64
from transformers import pipeline
import logging

app = FastAPI()
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

logging.basicConfig(level=logging.INFO)

@app.post("/process")
async def process_doc(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Solo se permiten archivos PDF"})
    try:
        contents = await file.read()
        with open("temp.pdf", "wb") as f:
            f.write(contents)

        doc = fitz.open("temp.pdf")
        full_text = ""
        images_b64 = []

        for page in doc:
            text = page.get_text()
            full_text += text
            for img in page.get_images(full=True):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ocr_text = pytesseract.image_to_string(Image.open(io.BytesIO(image_bytes)))
                full_text += "\n" + ocr_text
                b64_img = base64.b64encode(image_bytes).decode("utf-8")
                images_b64.append(f"data:image/png;base64,{b64_img}")

        summary = summarizer(full_text[:1024])[0]["summary_text"]
        logging.info(f"Resumen generado para: {file.filename}")

        return JSONResponse(content={"summary": summary, "images": images_b64[:3]})
    except Exception as e:
        logging.error(f"Error al procesar el archivo: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})