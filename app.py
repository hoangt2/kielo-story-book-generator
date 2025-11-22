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
        generate_story(status_callback=status_callback, level=level)
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
