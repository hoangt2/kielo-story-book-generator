import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY not found in environment variables.")
    # We don't exit here to allow import, but it will fail on usage if not set
    
genai.configure(api_key=GOOGLE_API_KEY)

def check_grammar(story_data):
    """
    Checks the grammar of the Finnish text in the story data using Gemini.
    Returns (is_valid, feedback).
    """
    print("Checking grammar...")
    
    # Extract Finnish text
    finnish_texts = []
    for page in story_data.get("pages", []):
        finnish_texts.append(f"Page {page.get('page_number')}: {page.get('text_fi')}")
    
    full_text = "\n".join(finnish_texts)
    
    prompt = f"""
    You are a strict Finnish grammar and style checker. Review the following story text for:
    1. **Grammatical errors** (case endings, verb conjugations, agreement)
    2. **Semantic errors** (words used incorrectly, nonsensical sentences)
    3. **Anglicisms / Finglish** (direct translations from English that are not natural Finnish)
    
    **SPECIFIC CHECKS:**
    - Watch out for "Minulla on hyvä" (I have good) -> SHOULD BE "Minulla on kaikki hyvin" or "Minulle kuuluu hyvää".
    - Watch out for "Otan bussia" (I take bus) -> SHOULD BE "Menen bussilla".
    - Ensure object cases (partitive vs genitive/accusative) are correct for the context.
    
    DO NOT judge vocabulary complexity or suggest simpler words. The vocabulary level is intentional.
    
    Story Text:
    {full_text}
    
    If the text is grammatically correct, matches natural Finnish idioms, and makes sense, respond with exactly:
    {{"valid": true, "feedback": "Grammar and meaning are correct"}}
    
    If there are grammatical, semantic, or idiomatic errors, respond with:
    {{"valid": false, "feedback": "Specific details about the error (e.g., 'Minulla on myös hyvä' is an unnatural direct translation, suggest 'Minulle kuuluu myös hyvää')"}}
    
    Return ONLY the valid JSON object.
    """
    
    try:
        model = genai.GenerativeModel('gemini-3.5-flash')
        response = model.generate_content(prompt)
        
        text = response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        
        return result.get("valid", False), result.get("feedback", "No feedback provided")
        
    except Exception as e:
        print(f"Error during grammar check: {e}")
        # Fail safe or pass? Let's fail safe to be sure.
        return False, f"Error during check: {str(e)}"

if __name__ == "__main__":
    # Test
    sample_story = {
        "level": "Beginner",
        "pages": [
            {"page_number": 1, "text_fi": "Minä olen kissa."}
        ]
    }
    valid, feedback = check_grammar(sample_story)
    print(f"Valid: {valid}, Feedback: {feedback}")
