import os
import google.generativeai as genai

def analyze_goals(text):
    """Analyze career goals using Gemini AI model."""
    if not text or not isinstance(text, str):
        return "⚠️ Please provide a valid career goal text."
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "⚠️ Gemini API key not set. Please enter it in the sidebar."
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = (
            f"Analyze the following career goal and extract the main skills, roles, and relevant keywords. "
            f"Present the analysis in a clear, user-friendly way:\n\n{text}"
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Error analyzing goal with AI: {str(e)}"
