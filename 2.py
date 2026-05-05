from flask import Flask, render_template, request
from flask_socketio import SocketIO
import os, time
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract
from docx import Document

app = Flask(__name__)
socketio = SocketIO(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def log(msg, level='info'):
    socketio.emit('log', {'message': msg, 'level': level})
    time.sleep(1)

def is_pdf_textual(pdf_path):
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        first_page = reader.pages[0]
        text = first_page.extract_text
        return bool(text and text.strip())
    except:
        return False
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload():
    file = request.files['file']
    filename = file.filename
    pdf_path = os.path.join(UPLOAD_FOLDER, filename)
    docx_path = pdf_path.replace('.pdf', '.docx')
    file.save(pdf_path)

    socketio.start_background_task(convert_pdf, pdf_path, docx_path)
    return '', 204

def convert_pdf(pdf_path, docx_path):
    log("شروع پردازش فایل...", "blue")

    if is_pdf_textual(pdf_path):
        log("تشخیص داده شد: فایل متنی است.", "green")
        log("در حال تبدیل با pdf2docx...", "blue")
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        log("تبدیل کامل شد (متنی).", "green")

    else:
        log("تشخیص داده شد: فایل تصویری است.", "blue")
        log("در حال تبدیل صفحات به تصویر برای OCR...", "blue")
        images = convert_from_path(pdf_path)
        document = Document()
        for i, image in enumerate(images):
            log(f"در حال OCR روی صفحه {i+1}...", "blue")
            text = pytesseract.image_to_string(image, lang='fas')
            document.add_paragraph(text)
        document.save(docx_path)
        log("استخراج متن کامل شد (OCR).", "green")

    log("پایان پردازش. فایل Word آماده است.", "green")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)


