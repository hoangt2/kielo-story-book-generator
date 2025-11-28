from flask import Flask, render_template, jsonify, send_from_directory, request
import threading
import os
import json
import time
from story_generator import main as generate_story

app = Flask(__name__)

# Global state for the generation process
generation_state = {
    "is_generating": False,
    "status": "Ready",
    "logs": []
}

def run_generation(level="Beginner"):
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
        success = generate_story(status_callback=status_callback, level=level)
        
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

@app.route('/api/generate', methods=['POST'])
def start_generation():
    if generation_state["is_generating"]:
        return jsonify({"error": "Already generating"}), 400
    
    data = request.get_json() or {}
    level = data.get("level", "Beginner")
    
    thread = threading.Thread(target=run_generation, args=(level,))
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
        
        # Save to history only when user explicitly archives
        from history_manager import save_to_history
        save_to_history(data)
        
        return jsonify({"message": "Story archived successfully", "path": archive_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
