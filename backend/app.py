from flask import Flask, Response, request, jsonify, send_from_directory
import base64
import os
import re
import time

import cv2 as cv
import numpy
from fpdf import FPDF
from deep_translator import GoogleTranslator

try:
    from suggestion import analyze_quality, get_image
except Exception:
    def analyze_quality(frame):
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        blur = cv.Laplacian(gray, cv.CV_64F).var()
        bright = numpy.mean(gray)
        ok = blur > 120 and 60 < bright < 220
        tips = []
        if blur <= 120:
            tips.append("Hold steady, image is blurry.")
        if bright <= 60:
            tips.append("Low light detected.")
        if bright >= 220:
            tips.append("Too bright, reduce glare.")
        return ok, tips, blur

    def get_image(frame):
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        gray = cv.resize(gray, None, fx=2, fy=2, interpolation=cv.INTER_CUBIC)
        return cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 11, 2)

from text import extract_text_from_image

FRONTEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
app = Flask(__name__, template_folder=FRONTEND, static_folder=FRONTEND)
STORE = {}


def serve(name):
    return send_from_directory(FRONTEND, name)


def decode_image(data_url):
    if not data_url:
        return None
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    try:
        buf = base64.b64decode(data_url)
        return cv.imdecode(numpy.frombuffer(buf, numpy.uint8), cv.IMREAD_COLOR)
    except Exception:
        return None


def summarize(text, max_sentences=3):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join([s for s in parts if s][:max_sentences]).strip()


def analyze_text_stats(text):
    words = re.findall(r"\b\w+\b", text)
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentence_count = max(len([s for s in sentences if s.strip()]), 1)
    word_count = len(words)
    character_count = len(text)
    syllables = 0
    for w in words:
        w = re.sub(r"[^a-z]", "", w.lower())
        if not w:
            continue
        vowels = "aeiouy"
        count = 0
        prev = False
        for ch in w:
            is_vowel = ch in vowels
            if is_vowel and not prev:
                count += 1
            prev = is_vowel
        if w.endswith("e") and count > 1:
            count -= 1
        syllables += max(count, 1)
    syllables = syllables or 1
    readability = 0.39 * (word_count / sentence_count) + 11.8 * (syllables / max(word_count, 1)) - 15.59
    return {
        "word_count": word_count,
        "character_count": character_count,
        "sentence_count": sentence_count,
        "readability_grade": max(1, round(readability))
    }


def extract_keywords(text, top_k=10):
    stop = {
        "the", "a", "an", "and", "or", "but", "if", "then", "else", "for", "to", "of",
        "in", "on", "at", "with", "as", "by", "from", "up", "down", "out", "over", "under",
        "is", "are", "was", "were", "be", "been", "being", "it", "this", "that", "these", "those",
        "we", "you", "he", "she", "they", "them", "his", "her", "their", "our", "your", "i",
        "me", "my", "mine", "ours", "yours", "so", "not", "no", "yes", "do", "does", "did",
        "can", "could", "would", "should", "will", "just", "than", "too", "very", "into", "about"
    }
    tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z][a-zA-Z0-9'-]*\b", text)]
    tokens = [t for t in tokens if t not in stop and len(t) > 2]
    counts = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    return [k for k, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_k]]


def generate_frames():
    idx = 0
    while True:
        cam = cv.VideoCapture(idx)
        if not cam.isOpened():
            idx += 1
            continue
        break

    while True:
        ok, frame = cam.read()
        if not ok:
            continue
        _, buf = cv.imencode(".jpg", frame)
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"

    cam.release()


@app.route("/")
@app.route("/landing.html")
def landing():
    return serve("landing.html")


@app.route("/scan.html")
def scan():
    return serve("scan.html")


@app.route("/results.html")
def results():
    return serve("results.html")


@app.route("/style.css")
def styles():
    return serve("style.css")


@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/analyze_and_capture", methods=["POST"])
def analyze_and_capture():
    payload = request.get_json(silent=True) or {}
    frame = decode_image(payload.get("image"))
    user_id = payload.get("user_id", "default_user")
    if frame is None:
        return jsonify({"status": "error", "message": "Invalid image data."}), 400

    ok, tips, _ = analyze_quality(frame)
    if not ok:
        return jsonify({"status": "analyzing", "suggestions": tips})

    images_dir = os.path.join(os.path.dirname(__file__), "images", "saved")
    os.makedirs(images_dir, exist_ok=True)
    filename = f"capture_{int(time.time())}.jpg"
    cv.imwrite(os.path.join(images_dir, filename), frame)

    image_path = f"images/saved/{filename}"
    text = extract_text_from_image(image_path=image_path)
    if not text:
        return jsonify({"status": "analyzing", "suggestions": [
            "No readable text detected. Try better lighting, move closer, or stabilize the camera."
        ]})

    STORE[user_id] = text
    return jsonify({"status": "success", "text": text, "filename": filename})


@app.route("/check_quality", methods=["POST"])
def check_quality():
    payload = request.get_json(silent=True) or {}
    frame = decode_image(payload.get("image"))
    if frame is None:
        return jsonify({"status": "error", "message": "Invalid image data."}), 400
    ok, tips, _ = analyze_quality(frame)
    return jsonify({"status": "ok", "is_good": ok, "suggestions": tips})


@app.route("/api/get_extracted_text", methods=["GET"])
def get_extracted_text():
    user_id = request.args.get("user_id", "default_user")
    text = STORE.get(user_id, "") or extract_text_from_image()
    return jsonify({"status": "success", "text": text})


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    if not text:
        return jsonify({"status": "error", "message": "No text provided."}), 400
    return jsonify({"status": "success", "summary": summarize(text)})


@app.route("/api/translate", methods=["POST"])
def api_translate():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    target = (payload.get("target_language") or "en").strip()
    if not text:
        return jsonify({"status": "error", "message": "No text provided."}), 400
    translated = GoogleTranslator(source="auto", target=target).translate(text)
    return jsonify({"status": "success", "translated_text": translated})


@app.route("/api/analyze_text", methods=["POST"])
def api_analyze_text():
    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    if not text:
        return jsonify({"status": "error", "message": "No text provided."}), 400
    return jsonify(analyze_text_stats(text))


@app.route("/api/get_keywords", methods=["POST"])
def api_get_keywords():
    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    if not text:
        return jsonify({"status": "error", "message": "No text provided."}), 400
    return jsonify({"keywords": extract_keywords(text)})


@app.route("/api/export_pdf", methods=["POST"])
def api_export_pdf():
    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    if not text:
        return jsonify({"status": "error", "message": "No text provided."}), 400
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.splitlines() or [text]:
        pdf.multi_cell(0, 8, line)
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return jsonify({"pdf_base64": base64.b64encode(pdf_bytes).decode("utf-8")})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)