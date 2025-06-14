import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Set custom download path for environments like Streamlit Cloud
NLTK_DATA_PATH = "/tmp/nltk_data"
nltk.data.path.append(NLTK_DATA_PATH)

# Download required resources if missing
for resource in ['punkt', 'stopwords']:
    try:
        nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' else f'corpora/{resource}')
    except LookupError:
        nltk.download(resource, download_dir=NLTK_DATA_PATH)

def analyze_goals(text):
    """Analyze career goals and extract meaningful keywords."""
    if not text or not isinstance(text, str):
        return "⚠️ Please provide a valid career goal text."
        
    try:
        # Clean and normalize text
        text = text.lower().strip()
        if not text:
            return "⚠️ Empty goal text provided."
            
        # Tokenize and filter words
        words = word_tokenize(text, language='english')
        filtered_words = [
            word for word in words
            if word.isalnum() and 
            word not in stopwords.words('english') and
            len(word) > 2
        ]
        
        # Extract unique keywords
        keywords = sorted(set(filtered_words))
        
        if not keywords:
            return "⚠️ No meaningful keywords extracted from your goal. Please provide more specific details."
            
        # Categorize
        tech_keywords = [k for k in keywords if any(tech in k for tech in ['dev', 'code', 'program', 'software', 'data', 'ai', 'ml', 'web', 'cloud'])]
        role_keywords = [k for k in keywords if any(role in k for role in ['engineer', 'developer', 'architect', 'manager', 'analyst', 'designer'])]
        other_keywords = [k for k in keywords if k not in tech_keywords and k not in role_keywords]
        
        output = "🔍 Keywords extracted from your goal:\n\n"
        if tech_keywords:
            output += f"💻 Technical Skills: {', '.join(tech_keywords)}\n"
        if role_keywords:
            output += f"👨‍💼 Roles: {', '.join(role_keywords)}\n"
        if other_keywords:
            output += f"📌 Other Keywords: {', '.join(other_keywords)}"
            
        return output
        
    except Exception as e:
        return f"⚠️ Error analyzing goal: {str(e)}"
