from flask import Flask, render_template, jsonify, send_from_directory, request
import threading
import os
import json
import time
from story_generator import main as generate_story, get_current_theme

app = Flask(__name__)

# Global state for the generation process
generation_state = {
    "is_generating": False,
    "status": "Ready",
    "logs": []
}

def run_generation(level="A1", theme_category=None, custom_topic=None, page_count=10, custom_setting=None, aspect_ratio=None, prompts_only=False):
    global generation_state
    generation_state["is_generating"] = True
    generation_state["status"] = "Starting..."
    generation_state["logs"] = []

    def status_callback(message):
        generation_state["status"] = message
        generation_state["logs"].append(message)
        print(f"[WEB] {message}")

    try:
        # Clean up first? Maybe optional.
        # For now, just run generation
        success = generate_story(status_callback=status_callback, level=level, theme_category=theme_category, custom_topic=custom_topic, page_count=page_count, custom_setting=custom_setting, aspect_ratio=aspect_ratio, prompts_only=prompts_only)
        
        # Check if generation failed
        if not success:
            generation_state["status"] = "Error: Failed to generate story after multiple attempts. Please retry."
        else:
            generation_state["status"] = "Complete"
    except Exception as e:
        generation_state["status"] = f"Error: {str(e)}"
        generation_state["logs"].append(f"Error: {str(e)}")
    finally:
        generation_state["is_generating"] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/themes')
def get_themes():
    """Returns available theme categories for the UI dropdown."""
    from prompts import get_theme_categories
    return jsonify(get_theme_categories())

@app.route('/api/suggestions')
def suggest_topics():
    """
    Returns topic suggestions for the requested difficulty level.

    The model is only called when ideas are actually asked for: a cold level
    generates one batch, `?refresh=1` generates another, and `?cached=1` never
    generates at all. Generated batches are cached per level, and the built-in
    list stands in whenever generation is skipped or fails.
    """
    from topic_suggestions import get_suggestions, get_level_hint

    level = request.args.get("level", "A1")
    refresh = request.args.get("refresh") == "1"      # always generate a new batch
    cached_only = request.args.get("cached") == "1"   # never call the model
    try:
        count = int(request.args.get("count", 6))
    except (TypeError, ValueError):
        count = 6
    count = max(3, min(10, count))

    suggestions, source = get_suggestions(
        level, count=count, refresh=refresh, allow_generate=not cached_only)
    return jsonify({
        "level": level,
        "hint": get_level_hint(level),
        "source": source,
        "suggestions": suggestions,
    })

@app.route('/api/generate', methods=['POST'])
def start_generation():
    if generation_state["is_generating"]:
        return jsonify({"error": "Already generating"}), 400
    
    data = request.get_json() or {}
    level = data.get("level", "A1")
    theme_category = data.get("theme_category", None)
    custom_topic = data.get("custom_topic", None)
    page_count = int(data.get("page_count", 10))
    
    custom_setting = data.get("custom_setting", None)
    aspect_ratio = data.get("aspect_ratio", None)
    prompts_only = data.get("prompts_only", False)
    
    # Normalize theme_category (empty string or "random" = None)
    if theme_category in [None, "", "random"]:
        theme_category = None
    
    thread = threading.Thread(target=run_generation, args=(level, theme_category, custom_topic, page_count, custom_setting, aspect_ratio, prompts_only))
    thread.start()
    return jsonify({"message": "Generation started"})

@app.route('/api/status')
def get_status():
    return jsonify(generation_state)

@app.route('/api/story')
def get_story():
    # Return the story.json content
    try:
        with open("output/data/story.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "No story found"}), 404

@app.route('/output/<path:filename>')
def serve_output(filename):
    return send_from_directory('output', filename)

import shutil
import datetime

@app.route('/api/archive', methods=['POST'])
def archive_story():
    try:
        # Load story data to get title
        with open("output/data/story.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        title = data.get("title_en", "Untitled")
        safe_title = "".join(x for x in title if x.isalnum() or x in (' ', '-', '_')).strip().replace(' ', '_')
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        archive_name = f"{timestamp}_{safe_title}"
        archive_path = os.path.join("archives", archive_name)
        
        # Create archive directory structure
        os.makedirs(os.path.join(archive_path, "data"), exist_ok=True)
        
        # Copy specific files/directories only
        # 1. Copy cards directory
        if os.path.exists("output/cards"):
            shutil.copytree("output/cards", os.path.join(archive_path, "cards"))
        
        # 2. Copy images directory
        if os.path.exists("output/images"):
            shutil.copytree("output/images", os.path.join(archive_path, "images"))
        
        # 3. Copy story.json
        if os.path.exists("output/data/story.json"):
            shutil.copy2("output/data/story.json", os.path.join(archive_path, "data", "story.json"))
        
        # 4. Copy story.pdf
        if os.path.exists("output/story.pdf"):
            shutil.copy2("output/story.pdf", os.path.join(archive_path, "story.pdf"))
        
        # Save to history with theme info
        from history_manager import save_to_history
        current_theme = get_current_theme()
        save_to_history(data, theme=current_theme)
        
        return jsonify({"message": "Story archived successfully", "path": archive_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/regenerate_image', methods=['POST'])
def regenerate_image():
    if generation_state["is_generating"]:
        return jsonify({"error": "Cannot regenerate while story is generating"}), 400
        
    data = request.get_json() or {}
    page_number = data.get("page_number")
    aspect_ratio = data.get("aspect_ratio", None)
    
    if not page_number:
        return jsonify({"error": "Page number is required"}), 400
        
    try:
        from story_generator import regenerate_page_image
        success, message = regenerate_page_image(int(page_number), aspect_ratio=aspect_ratio)
        
        if success:
            return jsonify({"message": "Image regenerated successfully", "path": message})
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

