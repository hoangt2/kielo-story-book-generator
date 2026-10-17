import os
import json
import argparse
from dotenv import load_dotenv
import google.generativeai as genai
from google import genai as imagen_client
from google.genai import types
from prompts import IMAGE_STYLE_GUIDE
from cinematography import camera_directive, camera_reminder, framing_note, fullbleed_lead
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
from history_manager import load_history, save_to_history, get_used_themes
from cleanup import cleanup
from languages import DEFAULT_LANGUAGE, LANGUAGES, normalize_language, text_key, title_key

def generate_story_concept(level="A1", theme_category=None, custom_topic=None, page_count=10, custom_setting=None, grammar_feedback=None, language=DEFAULT_LANGUAGE):
    """Generates the story structure using Gemini Pro."""
    global _current_theme
    language = normalize_language(language)

    theme_msg = theme_category or 'random'
    if custom_topic:
        theme_msg = f"Custom: {custom_topic}"

    print(f"Generating {LANGUAGES[language]['name']} story concept for {level} level (theme: {theme_msg}, pages: {page_count}, setting: {custom_setting})...")
    
    # Load history and used themes
    history = load_history()
    used_themes = get_used_themes()
    
    model = genai.GenerativeModel('gemini-3.5-flash')
    from prompts import get_story_prompt, select_theme
    
    # Select theme first so we can store it (even if we override it with custom topic)
    # If custom topic is present, we might still want a base theme for seasoning/setting if the user didn't specify?
    # Or we construct a "custom" theme object.
    
    if custom_topic or custom_setting:
        _current_theme = {
            "category": "custom",
            "season": "Any",
            "setting": custom_setting or "User defined",
            "activity": custom_topic or "User defined",
            "mood": "engaging"
        }
    else:
        _current_theme = select_theme(category=theme_category, used_themes=used_themes, language=language)

    print(f"Selected theme: {_current_theme.get('setting', 'Custom')} - {_current_theme.get('activity', custom_topic)}")

    # Pass history and theme info to prompt
    prompt = get_story_prompt(
        level,
        previous_stories=history,
        theme_category=theme_category,
        used_themes=used_themes,
        custom_topic=custom_topic,
        page_count=page_count,
        custom_setting=custom_setting,
        grammar_feedback=grammar_feedback,
        language=language
    )

    response = model.generate_content(prompt)

    try:
        # Clean up markdown code blocks if present
        text = response.text.replace("```json", "").replace("```", "").strip()
        story_data = json.loads(text)
        # Record the language so later steps (cards, prompts export, regenerate) pick the right text
        story_data["language"] = language
        return story_data
    except json.JSONDecodeError:
        print("Error: Failed to parse JSON from Gemini response.")
        print("Raw response:", response.text)
        return None

def get_current_theme():
    """Returns the theme used for the current generation session."""
    return _current_theme

# Supported aspect ratios and their canvas dimensions
ASPECT_RATIOS = {
    "9:16": {"label": "Vertical (9:16)", "width": 1080, "height": 1920},
    "1:1":  {"label": "Square (1:1)", "width": 1080, "height": 1080},
    "4:3":  {"label": "Landscape 4:3", "width": 1440, "height": 1080},
    "3:4":  {"label": "Portrait 3:4", "width": 1080, "height": 1440},
    "16:9": {"label": "Widescreen (16:9)", "width": 1920, "height": 1080},
}
DEFAULT_ASPECT_RATIO = "9:16"

def main(status_callback=None, level="A1", max_retries=5, theme_category=None, custom_topic=None, page_count=10, custom_setting=None, aspect_ratio=None, prompts_only=False, language=DEFAULT_LANGUAGE):
    def log(message):
        print(message)
        if status_callback:
            status_callback(message)

    if aspect_ratio is None:
        aspect_ratio = DEFAULT_ASPECT_RATIO

    parser = argparse.ArgumentParser(description="Story Book Generator (Finnish or Swedish)")
    parser.add_argument("--output_dir", default="output", help="Directory to save results")
    parser.add_argument("--language", default=language, choices=list(LANGUAGES.keys()), help="Language of the story text (default: fi)")
    parser.add_argument("--level", default=level, choices=["A1", "A2", "B1", "B2", "C1", "C2"], help="CEFR language level (default: A1)")
    parser.add_argument("--max_retries", type=int, default=max_retries, help="Maximum number of retries for grammar check")
    parser.add_argument("--theme", default=theme_category, help="Theme category (winter, spring, summer, autumn, everyday, special)")
    parser.add_argument("--topic", default=custom_topic, help="Custom topic for the story")
    parser.add_argument("--pages", type=int, default=page_count, help="Number of pages for the story")
    parser.add_argument("--setting", default=custom_setting, help="Custom setting for the story")
    parser.add_argument("--aspect-ratio", default=aspect_ratio, choices=list(ASPECT_RATIOS.keys()), help="Image aspect ratio (default: 9:16)")
    parser.add_argument("--prompts-only", action="store_true", default=prompts_only, help="Export image prompts only (no image generation)")
    
    # Check if running from script or module
    try:
        args = parser.parse_args()
    except:
        # Create a dummy namespace if parsing fails (e.g. when called from app.py)
        args = argparse.Namespace(
            output_dir="output", 
            level=level, 
            max_retries=max_retries, 
            theme=theme_category,
            topic=custom_topic,
            pages=page_count,
            setting=custom_setting,
            aspect_ratio=aspect_ratio,
            prompts_only=prompts_only,
            language=language,
        )

    args.language = normalize_language(args.language)

    # Clean up old output before starting
    log("Cleaning up previous output...")
    cleanup(args.output_dir)

    # 1. Generate Story with Retry Loop
    grammar_feedback = None  # Accumulated grammar feedback for retries
    for attempt in range(1, args.max_retries + 1):
        theme_label = args.theme or "random"
        if args.topic:
            theme_label = f"Custom: {args.topic}"

        log(f"Generating {LANGUAGES[args.language]['name']} story concept for {args.level} level, theme: {theme_label}, pages: {args.pages}, setting: {args.setting} (Attempt {attempt}/{args.max_retries})...")

        story = generate_story_concept(level=args.level, theme_category=args.theme, custom_topic=args.topic, page_count=args.pages, custom_setting=args.setting, grammar_feedback=grammar_feedback, language=args.language)
        if not story:
            log("Failed to generate story concept. Retrying...")
            continue

        # 2. Verify Grammar
        log("Verifying grammar...")
        is_valid, feedback = check_grammar(story, language=args.language)

        if is_valid:
            log("Grammar check passed!")

            if args.prompts_only:
                export_prompts(story, args.output_dir, status_callback)
            else:
                process_story(story, args.output_dir, status_callback, aspect_ratio=args.aspect_ratio)
            return True  # Success
        else:
            log(f"Grammar check failed: {feedback}")
            grammar_feedback = feedback  # Feed back for next attempt
            log("Retrying with grammar feedback...")
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

def _safe_name(name):
    return "".join(x for x in name if x.isalnum())


def find_character_models(characters, images_dir):
    """Returns [(name, path)] for every character whose model sheet exists in images_dir."""
    found = []
    for char in characters:
        name = char.get("name", "Unknown")
        path = os.path.join(images_dir, f"character_model_{_safe_name(name)}.png")
        if os.path.exists(path):
            found.append((name, path))
    return found


def build_character_reference(models, output_path, height=768):
    """
    Returns one reference image covering EVERY character, so each page keeps all of
    them consistent (the image model only accepts one reference). One character: its
    model sheet is used as is. Several: the sheets are placed side by side, left to
    right in the order given, and saved to output_path.
    """
    if not models:
        return None
    if len(models) == 1:
        return models[0][1]
    from PIL import Image
    sheets = []
    for _, path in models:
        img = Image.open(path).convert("RGB")
        sheets.append(img.resize((max(1, int(img.width * height / img.height)), height)))
    combined = Image.new("RGB", (sum(s.width for s in sheets), height), "white")
    x = 0
    for s in sheets:
        combined.paste(s, (x, 0))
        x += s.width
    combined.save(output_path)
    return output_path


def character_context(characters, models=None):
    """
    The character text passed with every page prompt. One character: just its
    description (unchanged behaviour). Several: every description plus an explicit
    instruction to keep each one's face, hair, clothes and costume identical on every
    page, naming the order they appear in the side-by-side reference image.
    """
    if not characters:
        return ""
    if len(characters) == 1:
        return characters[0].get("description", "")
    lines = [f"{c.get('name', 'Unknown')}: {c.get('description', '')}" for c in characters]
    text = ("Recurring characters. Each one MUST keep exactly the same face, hair, beard, "
            "clothes and costume on every page, even when only part of them is visible: "
            + " ".join(lines))
    if models and len(models) > 1:
        order = ", ".join(name for name, _ in models)
        text += (f" The reference image shows the characters side by side, left to right: "
                 f"{order}. Match each character to the reference exactly.")
    return text


def generate_image(prompt, output_path, character_description="", reference_image_path=None, aspect_ratio=None):
    """Generates an image using Nano Banana (Gemini 2.5 Flash Image)."""
    if aspect_ratio is None:
        aspect_ratio = DEFAULT_ASPECT_RATIO
    print(f"Generating image for: {prompt[:50]}... (aspect ratio: {aspect_ratio})")
    
    try:
        # Use Nano Banana (Gemini 2.5 Flash Image) for image generation
        client = imagen_client.Client(api_key=GOOGLE_API_KEY)
        
        # Lead with the camera direction — buried mid-paragraph it gets ignored —
        # then the characters, the page's own description, the style guide, and
        # any framing advice this canvas needs (9:16 cards overlay text).
        full_prompt = (f"{fullbleed_lead(aspect_ratio)}{camera_directive(prompt)} {character_description} {prompt} "
                       f"{IMAGE_STYLE_GUIDE}{framing_note(aspect_ratio)}"
                       f"{camera_reminder(prompt)}")
        
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
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
            ),
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
        dims = ASPECT_RATIOS.get(aspect_ratio, ASPECT_RATIOS[DEFAULT_ASPECT_RATIO])
        img = Image.new('RGB', (dims["width"], dims["height"]), color = 'lightblue')
        d = ImageDraw.Draw(img)
        d.text((10,10), "Generated Image Placeholder", fill=(0,0,0))
        img.save(output_path)
        print("Created placeholder image due to API error.")
        return True

def looks_inset(image_path, band=0.03, white=235, max_white=0.35):
    """
    True when the picture is an inset illustration floating in white space (a white or
    near-white margin on any side) instead of filling the canvas. Looks at a thin band
    along each edge and flags the picture when one band is mostly white.
    """
    from PIL import Image
    im = Image.open(image_path).convert("RGB")
    w, h = im.size
    bw, bh = max(2, int(w * band)), max(2, int(h * band))
    bands = [im.crop((0, 0, w, bh)), im.crop((0, h - bh, w, h)),
             im.crop((0, 0, bw, h)), im.crop((w - bw, 0, w, h))]
    for b in bands:
        px = list(b.getdata())
        if sum(1 for p in px if min(p) > white) / len(px) > max_white:
            return True
    return False


def generate_image_fullbleed(prompt, output_path, character_description="", reference_image_path=None,
                             aspect_ratio=None, max_retries=2):
    """
    generate_image, but on 9:16 full-bleed cards a picture that came back inset with white
    margins is drawn again (up to max_retries more times) so the art fills the page.
    The last attempt is kept if every try is inset.
    """
    ok = generate_image(prompt, output_path, character_description, reference_image_path,
                        aspect_ratio=aspect_ratio)
    if not ok or aspect_ratio != "9:16":
        return ok
    for attempt in range(max_retries):
        try:
            inset = looks_inset(output_path)
        except Exception as e:
            print(f"Inset check skipped: {e}")
            return ok
        if not inset:
            return ok
        print(f"Picture has white margins; drawing it again ({attempt + 1}/{max_retries})...")
        ok = generate_image(prompt, output_path, character_description, reference_image_path,
                            aspect_ratio=aspect_ratio)
        if not ok:
            return ok
    return ok


def export_prompts(story, output_dir="output", status_callback=None):
    """
    Exports image prompts for manual image generation.
    Outputs character prompts first, then scene prompts for each page.
    """
    def log(message):
        print(message)
        if status_callback:
            status_callback(message)

    # Create output directories
    dirs = {
        "root": output_dir,
        "data": os.path.join(output_dir, "data")
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    lang = normalize_language(story.get("language"))
    log(f"Exporting prompts for: {story.get(title_key(lang))} / {story.get('title_en')}")

    # Save story JSON for reference
    with open(os.path.join(dirs["data"], "story.json"), "w", encoding="utf-8") as f:
        json.dump(story, f, indent=2, ensure_ascii=False)

    # Build prompts document
    lines = []
    lines.append(f"# Image Prompts for: {story.get(title_key(lang))} / {story.get('title_en')}")
    lines.append(f"# Generated for manual image creation")
    lines.append("")

    # --- Style Guide ---
    lines.append("=" * 80)
    lines.append("STYLE GUIDE (apply to all images)")
    lines.append("=" * 80)
    lines.append(IMAGE_STYLE_GUIDE.strip())
    lines.append("")

    # --- Character Prompts ---
    characters = story.get("characters", [])
    if not characters:
        desc = story.get("character_description")
        if desc:
            characters.append({"name": "Main", "description": desc})

    lines.append("=" * 80)
    lines.append("CHARACTER REFERENCE SHEETS")
    lines.append("=" * 80)
    lines.append("")

    for i, char in enumerate(characters, 1):
        name = char.get("name", "Unknown")
        desc = char.get("description", "")
        lines.append(f"--- Character {i}: {name} ---")
        lines.append(f"Character sheet showing the following character: {desc}. Multiple views if possible, white background.")
        lines.append("")
        # Also include a standalone prompt with style guide baked in
        lines.append(f"Full prompt (with style):")
        lines.append(f"Character sheet showing the following character: {desc}. Multiple views if possible, white background. {IMAGE_STYLE_GUIDE.strip()}")
        lines.append("")

    # --- Scene Prompts ---
    lines.append("=" * 80)
    lines.append("SCENE PROMPTS (per page)")
    lines.append("=" * 80)
    lines.append("")

    for page in story.get("pages", []):
        page_num = page.get("page_number")
        page_type = page.get("type", "story")
        text_target = page.get(text_key(lang), "")
        text_en = page.get("text_en", "")
        image_desc = page.get("image_description", "")

        lines.append(f"--- Page {page_num} ({page_type}) ---")
        lines.append(f"{LANGUAGES[lang]['name']}: {text_target}")
        lines.append(f"English: {text_en}")
        lines.append(f"")
        lines.append(f"Image prompt:")
        lines.append(f"{image_desc}")
        lines.append(f"")
        lines.append(f"Full prompt (with style):")
        lines.append(f"{image_desc} {IMAGE_STYLE_GUIDE.strip()}")
        lines.append("")

    # Write prompts file
    prompts_path = os.path.join(output_dir, "image_prompts.txt")
    with open(prompts_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    log(f"Image prompts saved to {prompts_path}")
    log(f"Total: {len(characters)} character(s), {len(story.get('pages', []))} scene(s)")
    log("Prompts export complete! Use these prompts to generate images manually.")


def process_story(story, output_dir="output", status_callback=None, aspect_ratio=None):
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

    lang = normalize_language(story.get("language"))
    print(f"Story Title: {story.get(title_key(lang))} / {story.get('title_en')}")
    
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

    # Every character goes into the reference image and the prompt text, so none
    # of them drifts from page to page (not just the first one).
    models = [(c.get("name", "Unknown"), character_models[c.get("name", "Unknown")])
              for c in characters if c.get("name", "Unknown") in character_models]
    main_model_path = build_character_reference(
        models, os.path.join(dirs["images"], "character_reference.png"))
    main_char_desc = character_context(characters, models)

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
        # All characters' descriptions and one combined reference go with every page
        success = generate_image_fullbleed(full_prompt, image_path, main_char_desc, main_model_path, aspect_ratio=aspect_ratio)
        
        if success:
            # Composite
            create_story_card(
                image_path,
                page.get(text_key(lang)),
                page.get("text_en"),
                final_path,
                aspect_ratio=aspect_ratio
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



def regenerate_page_image(page_number, output_dir="output", aspect_ratio=None):
    """
    Regenerates the image for a specific page using the saved story data.
    """
    try:
        data_path = os.path.join(output_dir, "data", "story.json")
        if not os.path.exists(data_path):
            print(f"Error: Story data not found at {data_path}")
            return False, "Story data not found"
            
        with open(data_path, "r", encoding="utf-8") as f:
            story = json.load(f)
            
        lang = normalize_language(story.get("language"))

        # Find the page
        page = next((p for p in story.get("pages", []) if p.get("page_number") == page_number), None)
        if not page:
            print(f"Error: Page {page_number} not found in story data")
            return False, f"Page {page_number} not found"
            
        print(f"Regenerating image for page {page_number}...")
        
        # Paths
        images_dir = os.path.join(output_dir, "images")
        cards_dir = os.path.join(output_dir, "cards")
        
        image_filename = f"page_{page_number}.png"
        image_path = os.path.join(images_dir, image_filename)
        final_filename = f"story_card_{page_number}.png"
        final_path = os.path.join(cards_dir, final_filename)
        
        # Get character context
        characters = story.get("characters", [])
        # Use every character's saved model sheet (side by side in one reference image)
        # and every description, so the redrawn page matches the rest of the story.
        models = find_character_models(characters, images_dir)
        main_model_path = build_character_reference(
            models, os.path.join(images_dir, "character_reference.png"))
        main_char_desc = character_context(characters, models)

        # Generate Image
        full_prompt = f"{page.get('image_description')}"
        success = generate_image_fullbleed(full_prompt, image_path, main_char_desc, main_model_path, aspect_ratio=aspect_ratio)
        
        if success:
            # Composite
            create_story_card(
                image_path,
                page.get(text_key(lang)),
                page.get("text_en"),
                final_path,
                aspect_ratio=aspect_ratio
            )
            # Re-compile PDF (optional but good to keep in sync)
            # from pdf_generator import compile_to_pdf
            # compile_to_pdf(cards_dir, os.path.join(output_dir, "story.pdf"))
            
            return True, final_path
        else:
            return False, "Failed to generate image"
            
    except Exception as e:
        print(f"Error regenerating image: {e}")
        return False, str(e)


if __name__ == "__main__":
    main()
