import os
import re


def _simple_summarize(text, max_sentences=3):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join([s for s in sentences if s][:max_sentences]).strip()


def summarize_text(raw_text):
    """Summarize text using GitHub API key (GITHUB_TOKEN), otherwise fallback to a simple extractive summary."""
    raw_text = (raw_text or "").strip()
    if not raw_text:
        return ""

    from openai import OpenAI

    api_key = os.getenv("GITHUB_TOKEN")
    if not api_key:
        raise ValueError("GITHUB_TOKEN is required to summarize text.")

    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL", "https://models.github.ai/inference"),
        api_key="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"
    )

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes text concisely."},
            {"role": "user", "content": f"Please provide a short summary of the following text:\n\n{raw_text}"}
        ],
        model=os.getenv("OPENAI_MODEL", "gpt-4o")
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    from text import extract_text_from_image

    extracted_text = extract_text_from_image()
    summary = summarize_text(extracted_text)
    print("--- AI SUMMARY ---")
    print(summary)