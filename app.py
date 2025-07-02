import streamlit as st
from analyzer import analyze_website
from bs4 import BeautifulSoup
import requests
import re

st.set_page_config(page_title="Website Copy Fixer", layout="centered")
st.markdown("## 🛠️ Website Copy Fixer")
st.markdown("Paste in a business website URL and get improved copy + site suggestions.")

url = st.text_input("Company Website URL", placeholder="https://example.com")

tone_options = [
    "Professional – For B2B, finance, legal, or formal corporate audiences",
    "Confident – For tech and agencies — assertive, clear, and powerful",
    "Conversational – For friendly coaches and approachable service businesses",
    "Authoritative – For medical, consulting, and trust-heavy industries",
    "Persuasive – For sales pages, opt-ins, and funnels",
    "Luxury / Premium – For upscale brands: real estate, fashion, interior design",
    "Modern & Clean – For design-forward startups and minimal studios"
]
selected_option = st.selectbox("Choose a Tone/Style for Improved Copy", tone_options)
tone = selected_option.split("–")[0].strip()

def scrape_original_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text(separator="\n", strip=True)[:3000]
    except Exception as e:
        return f"Error scraping site: {e}"

def guess_original_components(text):
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 20]
    headline = lines[0] if lines else "Not found"
    subheadline = lines[1] if len(lines) > 1 else "Not found"
    cta = next((l for l in lines if re.search(r"(contact|get started|book|schedule|learn more|order now)", l, re.I)), "Not found")
    return headline, subheadline, cta

def detect_copy_mistakes(text):
    checks = [
        ("⚠️ Very little copy found — add more text to explain what you do.", lambda t: len(t) < 200),
        ("⚠️ Avoid long paragraphs — break content into shorter chunks or bullets.", lambda t: any(len(p.split()) > 40 for p in t.split("\n") if len(p.split()) > 1)),
        ("⚠️ No clear CTA found — add a button like “Book Now” or “Start Free Trial”.", lambda t: not re.search(r"(book|contact|get started|schedule|learn more|order now|call now)", t.lower())),
        ("⚠️ Lacks direct connection — speak to the reader using 'you' or 'we'.", lambda t: not re.search(r"\b(we|you|your|our)\b", t.lower())),
        ("⚠️ Passive voice — try to make your sentences more direct and active.", lambda t: re.search(r"\b(is|was|were|be|been|being)\b\s+\w+ed", t.lower())),
        ("⚠️ Missing social proof — add logos, testimonials, or partner names.", lambda t: not re.search(r"(trusted by|clients|testimonials|partners|case studies|reviews)", t.lower())),
        ("⚠️ No mention of credentials or experience — add credibility markers.", lambda t: not re.search(r"(years|experience|certified|award|licensed)", t.lower())),
        ("⚠️ No subheadline detected — clarify your offer beneath your main headline.", lambda t: len(t.split("\n")) < 3),
        ("⚠️ No clear value proposition — highlight what makes you different.", lambda t: not re.search(r"(benefit|difference|why|value|solution)", t.lower())),
        ("⚠️ Generic opening — skip 'welcome to our website' and get to the point.", lambda t: "welcome to our website" in t.lower()),
        ("⚠️ Generic services — be specific about what you actually offer.", lambda t: re.search(r"(services|solutions)", t.lower()) and not re.search(r"(consulting|design|copywriting|marketing|cleaning|coaching|therapy|web|branding)", t.lower())),
        ("⚠️ No location mentioned — add a city or region if you’re targeting locals.", lambda t: not re.search(r"\b(new york|miami|chicago|los angeles|san francisco|houston|atlanta|boston|seattle|dallas|toronto|london)\b", t.lower()))
    ]
    return [msg for msg, check in checks if check(text)][:3]

def generate_suggestions_with_ai(text, tone):
    try:
        prompt = f"""You are a website copy expert. The following is the content of a business homepage. Please generate 10 specific, advanced suggestions to improve the site's messaging. Each tip should be unique, detailed, and written for a {tone} tone. Be practical and include specific ideas, but avoid repeating headlines, subheadlines, or CTA fixes. Format as a numbered list:\n\n{text}"""
        headers = {
            "Authorization": "Bearer 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",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://websitecopyfixer.streamlit.app",
            "X-Title": "Website Copy Fixer"
        }
        payload = {
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [
                {"role": "system", "content": "You are a marketing expert that helps businesses improve website copy."},
                {"role": "user", "content": prompt}
            ]
        }
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        output = res.json()["choices"][0]["message"]["content"]
        return [re.sub(r"^\s*\d+[\.\)]\s*", "", line.strip()) for line in output.split("\n") if line.strip()]
    except Exception as e:
        return [f"⚠️ Could not generate suggestions: {e}"]

if st.button("Fix My Website Copy") and url:
    with st.spinner("Analyzing website and improving copy..."):
        improved_copy, _ = analyze_website(url, tone=tone)
        original_text = scrape_original_text(url)
        original_headline, original_subheadline, original_cta = guess_original_components(original_text)
        detected_mistakes = detect_copy_mistakes(original_text)
        ai_suggestions = generate_suggestions_with_ai(original_text, tone)

    if isinstance(improved_copy, str) and improved_copy.startswith("Error"):
        st.error(improved_copy)
    else:
        st.markdown("### 🔁 Before vs After Messaging")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🔴 Original Website Copy")
            st.markdown(
                f"""
                <div style='background-color:#2c2c2c;padding:15px;border-radius:10px;color:#ccc; font-size:15px; line-height:1.6'>
                    <b>Original Headline (guessed):</b><br>{original_headline}<br><br>
                    <b>Original Subheadline:</b><br>{original_subheadline}<br><br>
                    <b>Original Call-to-Action:</b><br>{original_cta}
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown("### ✅ AI-Improved Copy")
            lines = improved_copy.split("\n")
            headline = next((l for l in lines if "headline" in l.lower()), "Not found")
            subheadline = next((l for l in lines if "subheadline" in l.lower()), "Not found")
            cta = next((l for l in lines if "call-to-action" in l.lower()), "Not found")
            st.markdown(
                f"""
                <div style='background-color:#f0f0f0;padding:15px;border-radius:10px;color:#111; font-size:15px; line-height:1.6'>
                    <b>Headline:</b><br>{headline}<br><br>
                    <b>Subheadline:</b><br>{subheadline}<br><br>
                    <b>Call-to-Action:</b><br>{cta}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("### 💡 Smart Suggestions to Improve Site Messaging")
        if ai_suggestions:
            if "suggestions to improve" in ai_suggestions[0].lower():
                st.markdown(f"**💬 {ai_suggestions[0]}**")
                ai_suggestions = ai_suggestions[1:]

            for i, tip in enumerate(ai_suggestions, 1):
                st.markdown(f"**{i}. {tip}**")

        if detected_mistakes:
            st.markdown("### 🚩 Common Copy Mistakes to Avoid")
            for mistake in detected_mistakes:
                st.markdown(
                    f"<div style='background-color:#4a3d00;padding:10px 15px;margin:10px 0;border-radius:8px;color:#ffd'>{mistake}</div>",
                    unsafe_allow_html=True
                )

        st.download_button("📥 Download Improved Copy", improved_copy, file_name="improved_website_copy.txt")