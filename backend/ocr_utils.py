import re
from collections import Counter
import pytesseract
from pytesseract import Output

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "else", "for", "to", "of",
    "in", "on", "at", "with", "as", "by", "from", "up", "down", "out", "over", "under",
    "is", "are", "was", "were", "be", "been", "being", "it", "this", "that", "these", "those",
    "we", "you", "he", "she", "they", "them", "his", "her", "their", "our", "your", "i",
    "me", "my", "mine", "ours", "yours", "so", "not", "no", "yes", "do", "does", "did",
    "can", "could", "would", "should", "will", "just", "than", "too", "very", "into", "about"
}


def clean_ocr_text(lines):
    cleaned_lines = []
    for line in lines:
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        if len(re.findall(r"[A-Za-z0-9]", line)) < 3:
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def ocr_with_confidence(image, min_conf=55, lang="eng"):
    data = pytesseract.image_to_data(
        image,
        output_type=Output.DICT,
        config="--oem 3 --psm 6",
        lang=lang
    )
    lines = []
    current_line = []
    last_line_num = None
    line_nums = data.get("line_num", [])
    for i, text in enumerate(data.get("text", [])):
        if not text.strip():
            continue
        try:
            conf_val = float(data.get("conf", ["-1"])[i])
        except Exception:
            conf_val = -1
        if conf_val < min_conf:
            continue
        line_num = line_nums[i] if i < len(line_nums) else None
        if last_line_num is None or line_num == last_line_num:
            current_line.append(text.strip())
        else:
            lines.append(" ".join(current_line))
            current_line = [text.strip()]
        last_line_num = line_num
    if current_line:
        lines.append(" ".join(current_line))
    return clean_ocr_text(lines)


def count_syllables(word):
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev:
            count += 1
        prev = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def analyze_text_stats(text):
    words = re.findall(r"\b\w+\b", text)
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentence_count = max(len([s for s in sentences if s.strip()]), 1)
    word_count = len(words)
    character_count = len(text)
    syllable_count = sum(count_syllables(w) for w in words) or 1
    readability = 0.39 * (word_count / sentence_count) + 11.8 * (syllable_count / max(word_count, 1)) - 15.59
    return {
        "word_count": word_count,
        "character_count": character_count,
        "sentence_count": sentence_count,
        "readability_grade": max(1, round(readability))
    }


def extract_keywords(text, top_k=10):
    tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z][a-zA-Z0-9'-]*\b", text)]
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]
    counts = Counter(tokens)
    return [w for w, _ in counts.most_common(top_k)]
