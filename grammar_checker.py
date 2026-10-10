import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

from languages import LANGUAGES, normalize_language, text_key

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY not found in environment variables.")
    # We don't exit here to allow import, but it will fail on usage if not set

genai.configure(api_key=GOOGLE_API_KEY)

def check_grammar(story_data, language="fi"):
    """
    Checks the grammar of the target-language text in the story data using Gemini.
    Returns (is_valid, feedback).
    """
    print("Checking grammar...")

    language = normalize_language(language or story_data.get("language"))
    L = LANGUAGES[language]
    key = text_key(language)

    # Extract the target-language text
    story_texts = []
    for page in story_data.get("pages", []):
        story_texts.append(f"Page {page.get('page_number')}: {page.get(key)}")

    full_text = "\n".join(story_texts)

    prompt = f"""
    You are a strict {L['adjective']} grammar and style checker. Review the following story text for:
    1. **Grammatical errors** (case endings, verb conjugations, agreement)
    2. **Semantic errors** (words used incorrectly, nonsensical sentences)
    3. **Anglicisms / English calques** (direct translations from English that are not natural {L['adjective']})

    **SPECIFIC CHECKS:**
    {L['grammar_checks']}

    DO NOT judge vocabulary complexity or suggest simpler words. The vocabulary level is intentional.

    Story Text:
    {full_text}

    If the text is grammatically correct, matches natural {L['adjective']} idioms, and makes sense, respond with exactly:
    {{"valid": true, "feedback": "Grammar and meaning are correct"}}

    If there are grammatical, semantic, or idiomatic errors, respond with:
    {{"valid": false, "feedback": "Specific details about the error ({L['grammar_example_feedback']})"}}

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
    for code in ("fi", "sv"):
        sample_story = {
            "level": "A1",
            "pages": [
                {"page_number": 1, text_key(code): LANGUAGES[code]["grammar_sample"]}
            ]
        }
        valid, feedback = check_grammar(sample_story, language=code)
        print(f"{code} -> Valid: {valid}, Feedback: {feedback}")
