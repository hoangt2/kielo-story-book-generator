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

def get_used_themes(limit=10):
    """
    Returns a list of recently used themes to avoid repetition.
    Each theme is a dict with 'setting', 'activity', and optionally 'season'.
    """
    if not os.path.exists(HISTORY_FILE):
        return []
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
            # Extract theme info from recent stories
            used_themes = []
            for story in history[-limit:]:
                theme_info = story.get("theme")
                if theme_info:
                    used_themes.append(theme_info)
            return used_themes
    except (json.JSONDecodeError, IOError):
        return []

def save_to_history(story_data, theme=None):
    """
    Saves a new story to the history file.
    
    Args:
        story_data: The full story JSON data
        theme: Optional theme dict that was used for generation (setting, activity, season, mood)
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
    }
    
    # Add theme info if provided
    if theme:
        entry["theme"] = {
            "setting": theme.get("setting"),
            "activity": theme.get("activity"),
            "season": theme.get("season"),
            "category": theme.get("category"),
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
    print("Used themes:", get_used_themes())
    save_to_history(
        {"title_fi": "Testi", "title_en": "Test", "characters": [{"name": "Matti"}]},
        theme={"setting": "a ski resort", "activity": "skiing", "season": "Winter", "category": "winter"}
    )
    print("Loading history after save:", load_history())
    print("Used themes after save:", get_used_themes())

