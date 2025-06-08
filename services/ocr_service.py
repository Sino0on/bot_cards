import pytesseract
import cv2
import numpy as np
from io import BytesIO

async def text_contains_number(file_bytes, target="4566"):
    image_bytes = np.asarray(bytearray(file_bytes.read()), dtype=np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    text = pytesseract.image_to_string(gray)
    return target in text



from pdf2image import convert_from_bytes

async def extract_text(file_bytes, is_pdf=False):
    if is_pdf:
        images = convert_from_bytes(file_bytes.read())
        text = ""
        for img in images:
            gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
            text += pytesseract.image_to_string(gray)
        return text
    else:
        image_bytes = np.asarray(bytearray(file_bytes.read()), dtype=np.uint8)
        image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return pytesseract.image_to_string(gray)
