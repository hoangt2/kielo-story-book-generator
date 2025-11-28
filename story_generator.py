import os
import json
import argparse
from dotenv import load_dotenv
import google.generativeai as genai
from google import genai as imagen_client
from google.genai import types
from prompts import IMAGE_STYLE_GUIDE
from image_composer import create_story_card
import time

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY not found in environment variables.")
    exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

from grammar_checker import check_grammar
from history_manager import load_history, save_to_history
from cleanup import cleanup

def generate_story_concept(level="Beginner"):
    """Generates the story structure using Gemini Pro."""
    print(f"Generating story concept for {level} level...")
    
    # Load history
    history = load_history()
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    from prompts import get_story_prompt
    
    # Pass history to prompt
    prompt = get_story_prompt(level, previous_stories=history)
    
    response = model.generate_content(prompt)
    
    try:
        # Clean up markdown code blocks if present
        text = response.text.replace("```json", "").replace("```", "").strip()
        story_data = json.loads(text)
        return story_data
    except json.JSONDecodeError:
        print("Error: Failed to parse JSON from Gemini response.")
        print("Raw response:", response.text)
        return None

def main(status_callback=None, level="Beginner", max_retries=3):
    def log(message):
        print(message)
        if status_callback:
            status_callback(message)

    parser = argparse.ArgumentParser(description="Finnish Story Generator")
    parser.add_argument("--output_dir", default="output", help="Directory to save results")
    parser.add_argument("--level", default=level, choices=["Beginner", "Intermediate", "Advanced"], help="Language difficulty level")
    parser.add_argument("--max_retries", type=int, default=max_retries, help="Maximum number of retries for grammar check")
    
    # Check if running from script or module
    try:
        args = parser.parse_args()
    except:
        # Create a dummy namespace if parsing fails (e.g. when called from app.py)
        args = argparse.Namespace(output_dir="output", level=level, max_retries=max_retries)

    # Clean up old output before starting
    log("Cleaning up previous output...")
    cleanup(args.output_dir)

    # 1. Generate Story with Retry Loop
    for attempt in range(1, args.max_retries + 1):
        log(f"Generating story concept for {args.level} level (Attempt {attempt}/{args.max_retries})...")
        
        story = generate_story_concept(level=args.level)
        if not story:
            log("Failed to generate story concept. Retrying...")
            continue
            
        # 2. Verify Grammar
        log("Verifying grammar...")
        is_valid, feedback = check_grammar(story)
        
        if is_valid:
            log("Grammar check passed!")
            
            process_story(story, args.output_dir, status_callback)
            return True  # Success
        else:
            log(f"Grammar check failed: {feedback}")
            log("Retrying generation...")
            time.sleep(1)
            
    log("Max retries reached. Failed to generate a grammatically correct story.")
    return False  # Failed

def generate_character_model(description, output_path):
    """Generates a character model sheet for consistency."""
    print(f"Generating character model for: {description}...")
    
    try:
        client = imagen_client.Client(api_key=GOOGLE_API_KEY)
        # Prompt for a character sheet to get a consistent reference
        prompt = f"Character sheet showing the following character(s): {description}. Multiple views if possible, white background. {IMAGE_STYLE_GUIDE}"
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=[prompt],
        )
        
        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                image.save(output_path)
                print(f"Character model saved to {output_path}")
                return True
        
        print("No image found in response.")
        return False
    except Exception as e:
        print(f"Error generating character model: {e}")
        return False

def generate_image(prompt, output_path, character_description="", reference_image_path=None):
    """Generates an image using Nano Banana (Gemini 2.5 Flash Image)."""
    print(f"Generating image for: {prompt[:50]}...")
    
    try:
        # Use Nano Banana (Gemini 2.5 Flash Image) for image generation
        client = imagen_client.Client(api_key=GOOGLE_API_KEY)
        
        # Combine character description with the specific page prompt and style guide
        full_prompt = f"{character_description} {prompt} {IMAGE_STYLE_GUIDE}"
        
        contents = [full_prompt]
        
        # Add reference image if provided
        if reference_image_path and os.path.exists(reference_image_path):
            try:
                from PIL import Image
                ref_img = Image.open(reference_image_path)
                contents.append(ref_img)
                print("Using reference image for consistency.")
            except Exception as e:
                print(f"Could not load reference image: {e}")

        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=contents,
        )
        
        # Extract and save the image from the response
        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                image.save(output_path)
                print(f"Image saved to {output_path}")
                return True
        
        print("No image found in response.")
        return False
            
    except Exception as e:
        print(f"Error generating image: {e}")
        # Fallback for testing/mocking if API fails or model not found
        # Create a dummy image for flow verification
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (1024, 1024), color = 'lightblue')
        d = ImageDraw.Draw(img)
        d.text((10,10), "Generated Image Placeholder", fill=(0,0,0))
        img.save(output_path)
        print("Created placeholder image due to API error.")
        return True

def process_story(story, output_dir="output", status_callback=None):
    """
    Processes a generated story concept: generates images, cards, and PDF.
    """
    def log(message):
        print(message)
        if status_callback:
            status_callback(message)

    # Create main output directory and subdirectories
    dirs = {
        "root": output_dir,
        "images": os.path.join(output_dir, "images"),
        "cards": os.path.join(output_dir, "cards"),
        "data": os.path.join(output_dir, "data")
    }
    
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    print(f"Story Title: {story.get('title_fi')} / {story.get('title_en')}")
    
    # Save JSON for reference
    with open(os.path.join(dirs["data"], "story.json"), "w", encoding="utf-8") as f:
        json.dump(story, f, indent=2, ensure_ascii=False)

    # 2. Generate Character Models
    characters = story.get("characters", [])
    character_models = {} # Map name -> path

    if not characters:
        # Fallback for old format or empty list
        desc = story.get("character_description")
        if desc:
            characters.append({"name": "Main", "description": desc})

    for char in characters:
        name = char.get("name", "Unknown")
        desc = char.get("description", "")
        safe_name = "".join(x for x in name if x.isalnum())
        
        log(f"Processing character: {name}")
        model_path = os.path.join(dirs["images"], f"character_model_{safe_name}.png")
        
        if generate_character_model(desc, model_path):
            character_models[name] = model_path
        else:
            log(f"Failed to generate model for {name}")

    # Main character description for fallback/context
    main_char_desc = characters[0].get("description", "") if characters else ""
    main_model_path = list(character_models.values())[0] if character_models else None

    # 3. Process Pages
    for page in story.get("pages", []):
        page_num = page.get("page_number")
        log(f"Processing Page {page_num}...")
        
        # Paths
        image_filename = f"page_{page_num}.png"
        image_path = os.path.join(dirs["images"], image_filename)
        final_filename = f"story_card_{page_num}.png"
        final_path = os.path.join(dirs["cards"], final_filename)

        # Generate Image
        full_prompt = f"{page.get('image_description')}"
        # We pass the main character's description as a base, but the prompt should now be verbose enough
        success = generate_image(full_prompt, image_path, main_char_desc, main_model_path)
        
        if success:
            # Composite
            create_story_card(
                image_path, 
                page.get("text_fi"), 
                page.get("text_en"), 
                final_path
            )
        
        # Sleep to avoid rate limits
        time.sleep(2)

    log("Story generation complete!")

    # 4. Compile PDF
    log("Compiling PDF...")
    from pdf_generator import compile_to_pdf
    pdf_path = os.path.join(dirs["root"], "story.pdf")
    compile_to_pdf(dirs["cards"], pdf_path)
    log("All done! PDF created.")



if __name__ == "__main__":
    main()
