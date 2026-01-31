import cv2
import numpy as np

def analyze_quality(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Blur Detection
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    is_sharp = blur_score > 80
    
    # Lighting Detection
    avg_brightness = np.mean(gray)
    is_well_lit = 50 < avg_brightness < 230
    
    suggestions = []
    if not is_sharp:
        suggestions.append("Hold steady or move closer. Image looks blurry.")
    if avg_brightness <= 50:
        suggestions.append("Low light detected. Increase lighting or avoid shadows.")
    if avg_brightness >= 230:
        suggestions.append("Too bright. Reduce glare or move away from light source.")
    
    return (is_sharp and is_well_lit), suggestions, blur_score

def get_image(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Upscale and Adaptive Threshold for Tesseract
    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    processed = cv2.adaptiveThreshold(
        resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    return processed