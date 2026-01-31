import pytesseract
from pathlib import Path
from PIL import Image

# Setup Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(image_path="images/saved", destination_folder="images/processed"):
    base_dir = Path(__file__).resolve().parent
    img_file = base_dir / image_path

    # If path is a folder, grab the first image
    if img_file.is_dir():
        img_file = next(img_file.iterdir(), None)

    if not img_file or not img_file.exists():
        return ""

    # Extract text
    text = pytesseract.image_to_string(Image.open(img_file)).strip()

    # Move to processed folder
    dest_dir = base_dir / destination_folder
    dest_dir.mkdir(parents=True, exist_ok=True)
    img_file.replace(dest_dir / img_file.name)

    return text

if __name__ == "__main__":
    print(extract_text_from_image())