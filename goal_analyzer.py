import re
import nltk
import os
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Global flag to track if NLTK data is downloaded
_nltk_data_downloaded = False

nltk.data.path.append("/tmp")
nltk.download('punkt', download_dir='/tmp')
nltk.download('stopwords', download_dir='/tmp')


def ensure_nltk_data():
    """Ensure NLTK data is downloaded only once."""
    global _nltk_data_downloaded
    
    if _nltk_data_downloaded:
        return
        
    try:
        # Check and download required NLTK data
        required_data = ['punkt', 'stopwords']
        for item in required_data:
            try:
                nltk.data.find(f'tokenizers/{item}' if item == 'punkt' else f'corpora/{item}')
            except LookupError:
                nltk.download(item, quiet=True)
        
        _nltk_data_downloaded = True
    except Exception as e:
        raise Exception(f"Failed to download NLTK data: {str(e)}")

def analyze_goals(text):
    """Analyze career goals and extract meaningful keywords."""
    if not text or not isinstance(text, str):
        return "⚠️ Please provide a valid career goal text."
        
    try:
        ensure_nltk_data()
        
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
            len(word) > 2  # Filter out very short words
        ]
        
        # Extract unique keywords
        keywords = sorted(set(filtered_words))
        
        if not keywords:
            return "⚠️ No meaningful keywords extracted from your goal. Please provide more specific details."
            
        # Format output with categories
        tech_keywords = [k for k in keywords if any(tech in k.lower() for tech in ['dev', 'code', 'program', 'software', 'data', 'ai', 'ml', 'web', 'cloud'])]
        role_keywords = [k for k in keywords if any(role in k.lower() for role in ['engineer', 'developer', 'architect', 'manager', 'analyst', 'designer'])]
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
