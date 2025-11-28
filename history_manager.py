import os
import json

HISTORY_FILE = "history.json"

def load_history(limit=5):
    """
    Loads the history of generated stories.
    Returns a list of dicts containing title and summary/theme.
    """
    if not os.path.exists(HISTORY_FILE):
        return []
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
            # Return only the last 'limit' stories to keep context manageable
            return history[-limit:]
    except (json.JSONDecodeError, IOError):
        return []

def save_to_history(story_data):
    """
    Saves a new story to the history file.
    """
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []
    
    # Extract relevant info
    entry = {
        "title_fi": story_data.get("title_fi"),
        "title_en": story_data.get("title_en"),
        "characters": [c.get("name") for c in story_data.get("characters", [])],
        # We assume the first page or a specific field might have a summary, 
        # but for now title + characters is a good proxy for "theme".
        # If we had a summary field in the JSON, we'd use that.
    }
    
    history.append(entry)
    
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Failed to save history: {e}")

if __name__ == "__main__":
    # Test
    print("Loading history:", load_history())
    save_to_history({"title_fi": "Testi", "title_en": "Test", "characters": [{"name": "Matti"}]})
    print("Loading history after save:", load_history())
