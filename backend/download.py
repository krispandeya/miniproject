from docx import Document
from pptx import Presentation
import pandas as pd
import csv
from fpdf import FPDF


from text import extract_text_from_image

user_choice = input("Enter format (docx, pptx, pdf, csv, html, txt, or xlsx): ").lower()
text = extract_text_from_image()

if user_choice == 'docx':
    doc = Document()
    doc.add_paragraph(text)
    doc.save("file.docx")

elif user_choice == 'pptx':
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.placeholders[1].text = text
    prs.save("file.pptx")

elif user_choice == 'xlsx':
    pd.DataFrame([{"Content": text}]).to_excel("file.xlsx", index=False)

elif user_choice == "pdf":
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.output("file.pdf")

elif user_choice == "csv":
    f = open("file.csv", "w", newline="")
    csv.writer(f).writerow([text])
    f.close()

elif user_choice == "html":
    open("file.html", "w").write(f"<html><body><p>{text}</p></body></html>")

elif user_choice == "txt":
    open("file.txt", "w").write(text)

else:
    print("Invalid choice! Please run again and pick docx, pptx, pdf, xlsx, csv, html, or txt.")

print(f"Finished! Your {user_choice} file is ready.")