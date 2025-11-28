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
    MARGIN = 100  # Margin on all 4 sides for TikTok safe area
    CONTENT_WIDTH = CANVAS_WIDTH - (2 * MARGIN)
    CONTENT_HEIGHT = CANVAS_HEIGHT - (2 * MARGIN)
    IMAGE_SIZE = CONTENT_WIDTH  # Square image within margins
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
        # Paste image with margin offset
        canvas.paste(img, (MARGIN, MARGIN))
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return

    # Font setup
    font_size_fi = 70
    font_size_en = 50
    
    font_fi = None
    font_en = None

    # Try to find a nice font
    font_candidates_bold = [
        "arialbd.ttf", 
        "Arial Bold", 
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf"
    ]
    font_candidates_reg = [
        "arial.ttf", 
        "Arial", 
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf"
    ]

    for font_name in font_candidates_bold:
        try:
            font_fi = ImageFont.truetype(font_name, font_size_fi)
            break
        except IOError:
            continue
            
    for font_name in font_candidates_reg:
        try:
            font_en = ImageFont.truetype(font_name, font_size_en)
            break
        except IOError:
            continue
            
    if font_fi is None:
        print("Custom bold font not found, using default.")
        try:
            font_fi = ImageFont.load_default(size=font_size_fi)
        except TypeError:
            font_fi = ImageFont.load_default()

    if font_en is None:
        print("Custom regular font not found, using default.")
        try:
            font_en = ImageFont.load_default(size=font_size_en)
        except TypeError:
            font_en = ImageFont.load_default()

    # Text positioning (account for margins)
    text_start_y = MARGIN + IMAGE_SIZE + 60  # Start below image with some spacing
    text_bottom_limit = CANVAS_HEIGHT - MARGIN - 20  # Leave margin at bottom
    max_width = CONTENT_WIDTH - (2 * PADDING)

    # Helper to wrap text based on actual pixel width
    def wrap_text_to_width(text, font, max_width):
        """Wrap text to fit within max_width pixels"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            # Try adding word to current line
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                # Current line is full, start new line
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

    # Helper to calculate text height
    def calculate_text_height(text, font, max_width):
        """Calculate total height needed for text"""
        lines = wrap_text_to_width(text, font, max_width)
        if not lines:
            return 0
        
        # Get line height from first line
        bbox = draw.textbbox((0, 0), lines[0], font=font)
        line_height = bbox[3] - bbox[1]
        
        # Total height = (number of lines * line height) + (spacing between lines)
        total_height = len(lines) * line_height + (len(lines) - 1) * 15
        return total_height

    # Helper to find optimal font size
    def find_optimal_font_size(text, initial_size, max_width, max_height, font_candidates, min_size=20):
        """Find the largest font size that fits the text within constraints"""
        current_size = initial_size
        
        while current_size >= min_size:
            # Try to load font at current size
            font = None
            for font_name in font_candidates:
                try:
                    font = ImageFont.truetype(font_name, current_size)
                    break
                except IOError:
                    continue
            
            if font is None:
                try:
                    font = ImageFont.load_default(size=current_size)
                except TypeError:
                    font = ImageFont.load_default()
            
            # Check if text fits
            height = calculate_text_height(text, font, max_width)
            if height <= max_height:
                return font, current_size
            
            # Reduce size and try again
            current_size -= 2
        
        # If we get here, return the minimum size font
        font = None
        for font_name in font_candidates:
            try:
                font = ImageFont.truetype(font_name, min_size)
                break
            except IOError:
                continue
        
        if font is None:
            try:
                font = ImageFont.load_default(size=min_size)
            except TypeError:
                font = ImageFont.load_default()
        
        return font, min_size

    # Helper to draw text block with wrapping
    def draw_text_block(text, font, start_y, color):
        """Draw text block and return final y position"""
        lines = wrap_text_to_width(text, font, max_width)
        current_y = start_y
        
        # Get line height
        if lines:
            bbox = draw.textbbox((0, 0), lines[0], font=font)
            line_height = bbox[3] - bbox[1]
        else:
            line_height = 0
        
        for line in lines:
            # Calculate text width to center it
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (CANVAS_WIDTH - text_width) / 2
            draw.text((x, current_y), line, font=font, fill=color)
            current_y += line_height + 15  # Line spacing
        
        return current_y

    # Calculate available space for both text blocks
    available_height = text_bottom_limit - text_start_y
    
    # Allocate space: 60% for Finnish, 40% for English
    finnish_max_height = available_height * 0.6
    english_max_height = available_height * 0.4
    
    # Find optimal font sizes
    font_fi, actual_size_fi = find_optimal_font_size(
        finnish_text, font_size_fi, max_width, finnish_max_height, font_candidates_bold
    )
    font_en, actual_size_en = find_optimal_font_size(
        english_text, font_size_en, max_width, english_max_height, font_candidates_reg
    )
    
    print(f"Finnish font size: {actual_size_fi}px, English font size: {actual_size_en}px")
    
    # Draw Finnish text
    current_y = draw_text_block(finnish_text, font_fi, text_start_y, TEXT_COLOR)
    
    # Add spacing between languages
    current_y += 30
    
    # Draw English text (Grey color for subtitle feel)
    draw_text_block(english_text, font_en, current_y, "#555555")

    # Save
    canvas.save(output_path)
    print(f"Saved story card to {output_path}")

if __name__ == "__main__":
    # Test
    create_story_card("test_image.png", "Tämä on testi.", "This is a test.", "test_card.png")
