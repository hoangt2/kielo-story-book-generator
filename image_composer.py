from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

def create_story_card(image_path, finnish_text, english_text, output_path):
    """
    Composites a square image and bilingual text into a 9:16 vertical card.
    """
    # Constants
    CANVAS_WIDTH = 1080
    CANVAS_HEIGHT = 1920
    IMAGE_SIZE = 1080
    BG_COLOR = "#FFFFFF"
    TEXT_COLOR = "#000000"
    PADDING = 60
    
    # Create canvas
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    
    # Load and resize image
    try:
        img = Image.open(image_path)
        img = img.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)
        canvas.paste(img, (0, 0))
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return

    # Font setup (Try to find a nice font, fallback to default)
    try:
        # Windows paths for fonts
        font_path_bold = "arialbd.ttf" 
        font_path_reg = "arial.ttf"
        
        font_fi = ImageFont.truetype(font_path_bold, 60)
        font_en = ImageFont.truetype(font_path_reg, 48)
    except IOError:
        print("Custom fonts not found, using default.")
        font_fi = ImageFont.load_default()
        font_en = ImageFont.load_default()

    # Text positioning
    text_start_y = IMAGE_SIZE + 100
    max_width = CANVAS_WIDTH - (2 * PADDING)

    # Helper to wrap and draw text
    def draw_text_block(text, font, start_y, color):
        lines = textwrap.wrap(text, width=30) # Approx char width for 60px font
        current_y = start_y
        for line in lines:
            # Calculate text width to center it
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (CANVAS_WIDTH - text_width) / 2
            draw.text((x, current_y), line, font=font, fill=color)
            current_y += bbox[3] - bbox[1] + 20 # Line spacing
        return current_y

    # Draw Finnish text
    current_y = draw_text_block(finnish_text, font_fi, text_start_y, TEXT_COLOR)
    
    # Add spacing between languages
    current_y += 40
    
    # Draw English text (Grey color for subtitle feel)
    draw_text_block(english_text, font_en, current_y, "#555555")

    # Save
    canvas.save(output_path)
    print(f"Saved story card to {output_path}")

if __name__ == "__main__":
    # Test
    create_story_card("test_image.png", "Tämä on testi.", "This is a test.", "test_card.png")
