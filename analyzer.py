import requests
from bs4 import BeautifulSoup

API_KEY = "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"

def scrape_website_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script/style tags
        for tag in soup(["script", "style"]):
            tag.decompose()

        # Get visible text
        text = soup.get_text(separator=" ", strip=True)
        return text[:3000]  # Limit to 3000 characters
    except Exception as e:
        return f"Error scraping site: {e}"

def analyze_website(url, tone="Professional"):
    raw_text = scrape_website_text(url)

    prompt = f"""
You are a website copy expert. Analyze the business website content below and rewrite:

1. A clearer, more persuasive Headline (in a **{tone.lower()}** tone).
2. A benefit-driven Subheadline.
3. A motivating Call-to-Action.
4. Then, suggest 3–5 ways to improve the site's messaging.

Website Content:
\"\"\"
{raw_text}
\"\"\"

Return your response in this format:

Headline: ...
Subheadline: ...
Call-to-Action: ...
Suggestions:
- ...
- ...
- ...
"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        data = response.json()

        if response.status_code != 200:
            return f"Error from OpenRouter: {data}", []

        content = data["choices"][0]["message"]["content"]

        # Parse AI response
        headline = extract_section(content, "Headline:")
        subheadline = extract_section(content, "Subheadline:")
        cta = extract_section(content, "Call-to-Action:")
        suggestions = extract_suggestions(content)

        improved_copy = f"Headline: {headline}\nSubheadline: {subheadline}\nCall-to-Action: {cta}"
        return improved_copy, suggestions

    except Exception as e:
        return f"❌ Exception: {str(e)}", []

def extract_section(text, label):
    try:
        start = text.index(label) + len(label)
        end = text.find("\n", start)
        return text[start:end].strip() if end != -1 else text[start:].strip()
    except ValueError:
        return "(Not found in AI response.)"

def extract_suggestions(text):
    if "Suggestions:" in text:
        lines = text.split("Suggestions:")[-1].strip().split("\n")
        return [line.strip("- ").strip() for line in lines if line.strip()]
    return []