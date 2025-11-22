from PIL import Image
import os

def compile_to_pdf(image_dir, output_path):
    """
    Compiles all story_card_*.png files in the directory into a single PDF.
    """
    print(f"Compiling PDF from {image_dir}...")
    
    images = []
    # Find all story card images
    files = [f for f in os.listdir(image_dir) if f.startswith("story_card_") and f.endswith(".png")]
    
    # Sort by page number (assuming format story_card_N.png)
    try:
        files.sort(key=lambda x: int(x.split("_")[2].split(".")[0]))
    except ValueError:
        print("Warning: Could not sort files numerically. Using default sort.")
        files.sort()

    if not files:
        print("No story cards found to compile.")
        return False

    try:
        # Open first image
        first_image = Image.open(os.path.join(image_dir, files[0]))
        first_image = first_image.convert("RGB") # Ensure RGB for PDF
        
        # Open rest of images
        image_list = []
        for f in files[1:]:
            img = Image.open(os.path.join(image_dir, f))
            img = img.convert("RGB")
            image_list.append(img)
            
        # Save as PDF
        first_image.save(output_path, save_all=True, append_images=image_list)
        print(f"PDF saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error compiling PDF: {e}")
        return False

if __name__ == "__main__":
    # Test
    compile_to_pdf("output/cards", "output/story.pdf")
