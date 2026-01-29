import logging
import os
from pathlib import Path
from PIL import Image
import pytesseract

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default location for the Tesseract binary on Windows; override with the TESSERACT_CMD env var.
DEFAULT_TESSERACT_PATH = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"


def configure_tesseract() -> None:
    """Configure pytesseract to point at the installed Tesseract executable."""
    tesseract_cmd = os.environ.get("TESSERACT_CMD", DEFAULT_TESSERACT_PATH)
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    if not Path(tesseract_cmd).exists():
        raise FileNotFoundError(
            "Tesseract executable not found. Install it or set TESSERACT_CMD to the binary path."
        )
def extract_text_from_image(
    image_path: str = "images/saved",
    destination_folder: str = "images/processed",
) -> str:
    try:
        configure_tesseract()

        # Convert input to an absolute Path object
        image_file = Path(image_path)
        base_dir = Path(__file__).resolve().parent
        if not image_file.is_absolute():
            image_file = base_dir / image_file

        if image_file.is_dir():
            candidates = sorted(
                p
                for p in image_file.iterdir()
                if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
            )
            if not candidates:
                raise FileNotFoundError(f"No image files found in: {image_file}")
            image_file = candidates[0]

        if not image_file.exists():
            raise FileNotFoundError(f"Image file not found: {image_file}")

        # 1. Open and extract text
        with Image.open(image_file) as img:
            extracted_text = pytesseract.image_to_string(img).strip()

        # 2. Dynamic Move (No hard-coded names)
        # Uses the original filename in the new directory
        destination_dir = Path(destination_folder)
        if not destination_dir.is_absolute():
            destination_dir = base_dir / destination_dir
        destination_dir.mkdir(parents=True, exist_ok=True)
        target_path = destination_dir / image_file.name
        image_file.replace(target_path)

        return extracted_text

    except Exception as exc:
        logger.exception("Failed to process image: %s", exc)
        return ""

if __name__ == "__main__":
    # Example usage; replace with your image path from app.py.
    # sample_image_path = "path/to/image/from/app.py"
    print(extract_text_from_image())