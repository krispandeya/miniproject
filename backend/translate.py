import pandas as pd
from deep_translator import GoogleTranslator
from text import extract_text_from_image

lang = pd.read_csv("backend/languages.csv")

def translate_extracted_text():
    try:
        text_to_translate = extract_text_from_image()

        target_lang = input("\nEnter the language code to translate to: (https://docs.google.com/spreadsheets/d/1jBqLYgmQxnCeiH3lGdKiapfwzZ6rP5KxK9L2SZHd4P8/edit?usp=sharing)")

        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(text_to_translate)
        print(translated_text)

    except:
        print("Translation failed")

if __name__ == "__main__":
    translate_extracted_text()