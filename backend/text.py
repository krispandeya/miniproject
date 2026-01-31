import cv2
import numpy as np
import os
import shutil
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def enhance_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_OPEN, kernel)
    enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
    return enhanced

def extract_text_with_confidence(img_path):
    if not os.path.isfile(img_path): 
        return "", 0.0
    img = cv2.imread(img_path)
    if img is None: 
        return "", 0.0
    
    enhanced = enhance_image(img)
    pil_img = Image.fromarray(enhanced)
    
    text = pytesseract.image_to_string(pil_img, lang='eng', config='--oem 3 --psm 6').strip()
    confidence = 0.7 if text else 0.0
    
    return text, confidence

def move_to_processed(img_path):
    try:
        dest = 'images/processed'
        os.makedirs(dest, exist_ok=True)
        new_path = os.path.join(dest, os.path.basename(img_path))
        shutil.copy2(img_path, new_path)
        if os.path.exists(img_path): 
            os.remove(img_path)
        return new_path
    except: 
        return None

def extract_text_from_image(image_dir="images/saved"):
    try:
        if not os.path.exists(image_dir):
            return "", 0.0
        for filename in os.listdir(image_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                img_path = os.path.join(image_dir, filename)
                text, conf = extract_text_with_confidence(img_path)
                if text:
                    move_to_processed(img_path)
                    return text, conf
                return "", conf
        return "", 0.0
    except Exception as e:
        print(f"Error: {e}")
        return "", 0.0