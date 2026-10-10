from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# Aspect ratio canvas configurations (shared with story_generator.py)
ASPECT_RATIO_CONFIGS = {
    "9:16": {"width": 1080, "height": 1920},
    "1:1":  {"width": 1080, "height": 1080},
    "4:3":  {"width": 1440, "height": 1080},
    "3:4":  {"width": 1080, "height": 1440},
    "16:9": {"width": 1920, "height": 1080},
}
DEFAULT_ASPECT_RATIO = "9:16"

# Font candidates
FONT_CANDIDATES_BOLD = [
    "arialbd.ttf", 
    "Arial Bold", 
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf"
]
FONT_CANDIDATES_REG = [
    "arial.ttf", 
    "Arial", 
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf"
]

def _load_font(candidates, size):
    """Try to load a font from the candidate list, fall back to default."""
    for font_name in candidates:
        try:
            return ImageFont.truetype(font_name, size)
        except IOError:
            continue
    # Fallback
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

# Some illustrations come back with a drawn frame: a light paper margin, often
# with a thin dark rule just inside it. On a full-bleed card that reads as a
# rendering bug, and in a split card it doubles the padding — so it gets cropped
# off before compositing. Deliberately conservative: a frame is thin and shows
# up on nearly every side, so a bright sky or a snowy edge is left alone.
_FRAME_MAX_TRIM = 0.15      # never remove more than 15% of a side
_FRAME_LIGHT_MIN = 190      # a paper margin is at least this bright (edges antialias)
_FRAME_DARK_MAX = 140       # the rule drawn inside it is at most this bright
_FRAME_MIN_SIDES = 3        # a real frame surrounds the artwork
_FRAME_SOFT_MAX_TRIM = 0.06  # a ruleless margin is only believed if it is thin


def _strip_is(img, box, kind):
    """True when every pixel in the 1px strip `box` is uniformly light/dark."""
    extrema = img.crop(box).getextrema()
    if kind == "light":
        return all(low >= _FRAME_LIGHT_MIN for low, _ in extrema)
    return all(high <= _FRAME_DARK_MAX for _, high in extrema)


def _frame_inset(img, side, require_rule=True):
    """
    Measures the drawn frame's thickness on one side, or 0 if there is none.

    `require_rule` demands a dark rule behind the bright margin, which is what
    tells a drawn frame apart from a pale sky. Once the other sides have proved
    a frame exists, the last side can be measured without it.
    """
    width, height = img.size
    span = height if side in ("top", "bottom") else width
    limit = int(span * _FRAME_MAX_TRIM)

    # `inset` shortens the strip at both ends. The dark rule stops where the
    # side margins begin, so its corners are still bright — testing the full
    # width would never see a uniformly dark line.
    def strip(offset, inset):
        if side == "top":
            return (inset, offset, width - inset, offset + 1)
        if side == "bottom":
            return (inset, height - offset - 1, width - inset, height - offset)
        if side == "left":
            return (offset, inset, offset + 1, height - inset)
        return (width - offset - 1, inset, width, height - inset)

    cross_span = width if side in ("top", "bottom") else height
    light_inset = int(cross_span * 0.02)
    rule_inset = int(cross_span * 0.20)

    offset = 0
    while offset < limit and _strip_is(img, strip(offset, light_inset), "light"):
        offset += 1

    # No margin here, or a bright region too thick to be one (sky, snow, wall).
    if offset == 0 or offset >= limit:
        return 0

    # A drawn frame puts a dark rule between the margin and the artwork. Requiring
    # it is what separates a real frame from a pale sky running off the edge.
    if not require_rule:
        return offset

    # The rule sits at the margin's inner edge, a couple of antialiased rows in.
    scan_limit = min(limit, offset + 5)
    while offset < scan_limit and not _strip_is(img, strip(offset, rule_inset), "dark"):
        offset += 1
    if offset >= scan_limit:
        return 0  # bright edge with no rule behind it — sky or snow, not a frame

    while offset < limit and _strip_is(img, strip(offset, rule_inset), "dark"):
        offset += 1
    return offset


def _trim_drawn_frame(img):
    """Crops a drawn border/margin off an illustration, if it has one."""
    if img.mode != "RGB":
        img = img.convert("RGB")

    sides = ("top", "bottom", "left", "right")
    span = {"top": img.height, "bottom": img.height, "left": img.width, "right": img.width}

    insets = {side: _frame_inset(img, side) for side in sides}
    if sum(1 for inset in insets.values() if inset > 0) >= _FRAME_MIN_SIDES:
        # A frame is confirmed; measure any side whose own rule was not clean
        # enough to see, so we do not crop three edges and leave a lopsided fourth.
        for side in sides:
            if insets[side] == 0:
                insets[side] = _frame_inset(img, side, require_rule=False)
    else:
        # No rule drawn, but some images come back with a soft light margin on
        # every side. Believe that only while it stays thin — then the worst case
        # is shaving a sliver of sky off an image that never had a margin.
        loose = {side: _frame_inset(img, side, require_rule=False) for side in sides}
        insets = {side: inset if 0 < inset <= span[side] * _FRAME_SOFT_MAX_TRIM else 0
                  for side, inset in loose.items()}
        if sum(1 for inset in insets.values() if inset > 0) < _FRAME_MIN_SIDES:
            return img

    box = (insets["left"], insets["top"],
           img.width - insets["right"], img.height - insets["bottom"])
    if box[2] - box[0] < img.width // 2 or box[3] - box[1] < img.height // 2:
        return img  # something is off; leave the image alone

    print(f"Trimmed drawn frame: {insets}")
    return img.crop(box)


def _wrap_text_to_width(draw, text, font, max_width):
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        
        if line_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def _calculate_text_height(draw, text, font, max_width, line_spacing=15):
    """Calculate total height needed for wrapped text."""
    lines = _wrap_text_to_width(draw, text, font, max_width)
    if not lines:
        return 0
    
    bbox = draw.textbbox((0, 0), lines[0], font=font)
    line_height = bbox[3] - bbox[1]
    total_height = len(lines) * line_height + (len(lines) - 1) * line_spacing
    return total_height

def _find_optimal_font_size(draw, text, initial_size, max_width, max_height, font_candidates, min_size=20):
    """Find the largest font size that fits the text within constraints."""
    current_size = initial_size
    
    while current_size >= min_size:
        font = _load_font(font_candidates, current_size)
        height = _calculate_text_height(draw, text, font, max_width)
        if height <= max_height:
            return font, current_size
        current_size -= 2
    
    return _load_font(font_candidates, min_size), min_size

def _draw_text_block(draw, text, font, start_y, color, canvas_width, max_width, line_spacing=15):
    """Draw a centered text block and return the final y position."""
    lines = _wrap_text_to_width(draw, text, font, max_width)
    current_y = start_y
    
    if lines:
        bbox = draw.textbbox((0, 0), lines[0], font=font)
        line_height = bbox[3] - bbox[1]
    else:
        line_height = 0
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (canvas_width - text_width) / 2
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += line_height + line_spacing
    
    return current_y

def _draw_text_block_with_shadow(draw, text, font, start_y, color, canvas_width, max_width, line_spacing=15, shadow_color="#00000080", shadow_offset=2):
    """Draw a centered text block with drop shadow for readability on images."""
    lines = _wrap_text_to_width(draw, text, font, max_width)
    current_y = start_y
    
    if lines:
        bbox = draw.textbbox((0, 0), lines[0], font=font)
        line_height = bbox[3] - bbox[1]
    else:
        line_height = 0
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (canvas_width - text_width) / 2
        # Draw shadow
        draw.text((x + shadow_offset, current_y + shadow_offset), line, font=font, fill=shadow_color)
        # Draw text
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += line_height + line_spacing
    
    return current_y


def create_story_card(image_path, main_text, english_text, output_path, aspect_ratio=None):
    """
    Composites an image and bilingual text into a story card.
    
    For 9:16 (default): Full-bleed image with text overlaid on a gradient at the bottom.
    For other ratios: Image at top with text area below.
    """
    if aspect_ratio is None:
        aspect_ratio = DEFAULT_ASPECT_RATIO
    
    config = ASPECT_RATIO_CONFIGS.get(aspect_ratio, ASPECT_RATIO_CONFIGS[DEFAULT_ASPECT_RATIO])
    CANVAS_WIDTH = config["width"]
    CANVAS_HEIGHT = config["height"]
    
    if aspect_ratio == "9:16":
        _create_fullbleed_card(image_path, main_text, english_text, output_path, CANVAS_WIDTH, CANVAS_HEIGHT)
    else:
        _create_split_card(image_path, main_text, english_text, output_path, CANVAS_WIDTH, CANVAS_HEIGHT)


def _create_fullbleed_card(image_path, main_text, english_text, output_path, canvas_width, canvas_height):
    """
    9:16 full-screen vertical card: image fills the entire canvas,
    text is overlaid on a dark gradient at the bottom.
    """
    MARGIN = 60
    PADDING = 40
    TEXT_ZONE_HEIGHT = int(canvas_height * 0.35)  # Bottom 35% for text overlay
    
    # Create canvas
    canvas = Image.new("RGB", (canvas_width, canvas_height), "#000000")
    
    # Load and resize image to fill canvas (cover mode)
    try:
        img = _trim_drawn_frame(Image.open(image_path))
        # Scale to cover the canvas
        img_ratio = img.width / img.height
        canvas_ratio = canvas_width / canvas_height
        
        if img_ratio > canvas_ratio:
            # Image is wider — fit to height, crop sides
            new_height = canvas_height
            new_width = int(canvas_height * img_ratio)
        else:
            # Image is taller — fit to width, crop top/bottom
            new_width = canvas_width
            new_height = int(canvas_width / img_ratio)
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center crop
        x_offset = (new_width - canvas_width) // 2
        y_offset = (new_height - canvas_height) // 2
        img = img.crop((x_offset, y_offset, x_offset + canvas_width, y_offset + canvas_height))
        
        canvas.paste(img, (0, 0))
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return
    
    # Draw gradient overlay at bottom for text readability
    gradient = Image.new("RGBA", (canvas_width, TEXT_ZONE_HEIGHT), (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient)
    
    for y in range(TEXT_ZONE_HEIGHT):
        # Gradient from transparent to semi-opaque black
        alpha = int(200 * (y / TEXT_ZONE_HEIGHT))
        gradient_draw.line([(0, y), (canvas_width, y)], fill=(0, 0, 0, alpha))
    
    # Paste gradient at the bottom
    canvas = canvas.convert("RGBA")
    canvas.paste(gradient, (0, canvas_height - TEXT_ZONE_HEIGHT), gradient)
    canvas = canvas.convert("RGB")
    
    draw = ImageDraw.Draw(canvas)
    
    # Text layout within the gradient zone
    max_text_width = canvas_width - (2 * (MARGIN + PADDING))
    text_start_y = canvas_height - TEXT_ZONE_HEIGHT + int(TEXT_ZONE_HEIGHT * 0.15)
    text_bottom_limit = canvas_height - MARGIN
    available_height = text_bottom_limit - text_start_y
    
    # Font sizing
    main_max_height = available_height * 0.6
    english_max_height = available_height * 0.35
    
    font_fi, actual_size_fi = _find_optimal_font_size(
        draw, main_text, 64, max_text_width, main_max_height, FONT_CANDIDATES_BOLD
    )
    font_en, actual_size_en = _find_optimal_font_size(
        draw, english_text, 44, max_text_width, english_max_height, FONT_CANDIDATES_REG
    )
    
    print(f"Main font size: {actual_size_fi}px, English font size: {actual_size_en}px (fullbleed)")
    
    # Draw main text (white with shadow)
    current_y = _draw_text_block_with_shadow(
        draw, main_text, font_fi, text_start_y, "#FFFFFF",
        canvas_width, max_text_width
    )
    
    current_y += 20
    
    # Draw English text (light grey with shadow)
    _draw_text_block_with_shadow(
        draw, english_text, font_en, current_y, "#CCCCCC",
        canvas_width, max_text_width
    )
    
    canvas.save(output_path)
    print(f"Saved fullbleed story card to {output_path}")


def _create_split_card(image_path, main_text, english_text, output_path, canvas_width, canvas_height):
    """
    Non-fullscreen layout: image at top, text below (used for 1:1, 4:3, 16:9, 3:4).
    """
    MARGIN = 60
    PADDING = 40
    BG_COLOR = "#FFFFFF"
    TEXT_COLOR = "#000000"
    
    # Image takes up 65% of height, text takes 35%
    image_area_height = int(canvas_height * 0.65)
    text_area_height = canvas_height - image_area_height
    
    canvas = Image.new("RGB", (canvas_width, canvas_height), BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    
    # Load and resize image to fill image area (cover mode)
    try:
        img = _trim_drawn_frame(Image.open(image_path))
        img_ratio = img.width / img.height
        area_ratio = canvas_width / image_area_height
        
        if img_ratio > area_ratio:
            new_height = image_area_height
            new_width = int(image_area_height * img_ratio)
        else:
            new_width = canvas_width
            new_height = int(canvas_width / img_ratio)
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        x_offset = (new_width - canvas_width) // 2
        y_offset = (new_height - image_area_height) // 2
        img = img.crop((x_offset, y_offset, x_offset + canvas_width, y_offset + image_area_height))
        
        canvas.paste(img, (0, 0))
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return
    
    # Text layout
    max_text_width = canvas_width - (2 * (MARGIN + PADDING))
    text_start_y = image_area_height + 30
    text_bottom_limit = canvas_height - MARGIN
    available_height = text_bottom_limit - text_start_y
    
    main_max_height = available_height * 0.6
    english_max_height = available_height * 0.35
    
    font_fi, actual_size_fi = _find_optimal_font_size(
        draw, main_text, 56, max_text_width, main_max_height, FONT_CANDIDATES_BOLD
    )
    font_en, actual_size_en = _find_optimal_font_size(
        draw, english_text, 40, max_text_width, english_max_height, FONT_CANDIDATES_REG
    )
    
    print(f"Main font size: {actual_size_fi}px, English font size: {actual_size_en}px (split)")
    
    # Draw main text
    current_y = _draw_text_block(
        draw, main_text, font_fi, text_start_y, TEXT_COLOR,
        canvas_width, max_text_width
    )
    
    current_y += 20
    
    # Draw English text (grey for subtitle feel)
    _draw_text_block(
        draw, english_text, font_en, current_y, "#555555",
        canvas_width, max_text_width
    )
    
    canvas.save(output_path)
    print(f"Saved split story card to {output_path}")


if __name__ == "__main__":
    # Test
    create_story_card("test_image.png", "Tämä on testi.", "This is a test.", "test_card.png")
