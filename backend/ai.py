import os
import openai
from text import extract_text_from_image

client = openai.OpenAI(
    base_url="https://models.github.ai/inference",
    api_key=os.getenv("GITHUB_TOKEN")
)

def summarize_text(raw_text):
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes text concisely."},
            {"role": "user", "content": f"Please provide a short summary of the following text:\n\n{raw_text}"}
        ],
        model="gpt-4o" 
    )
    return response.choices[0].message.content

extracted_text = extract_text_from_image()
summary = summarize_text(extracted_text)

print("--- AI SUMMARY ---")
print(summary)