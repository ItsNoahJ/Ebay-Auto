"""
Create test images for integration tests.
"""
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_text_image(filename: str, text: str, size=(800, 600), bg_color="white", text_color="black"):
    """Create an image with text."""
    # Create image
    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to use Arial font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except IOError:
        font = ImageFont.load_default()
    
    # Calculate text position to center it
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    # Draw text
    draw.text((x, y), text, fill=text_color, font=font)
    
    # Save image
    img.save(filename)
    return filename

def main():
    """Create test images."""
    # Ensure test_images directory exists
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    # Create movie test image
    create_text_image(
        test_dir / "test_vhs_cover.jpg",
        "Back to the Future (1985)",
        (800, 1200)
    )
    
    # Create audio test image
    create_text_image(
        test_dir / "test_audio_cover.jpg",
        "Pink Floyd - The Wall",
        (800, 800)
    )
    
    # Create blank test image
    Image.new('RGB', (100, 100), 'white').save(test_dir / "blank.jpg")
    
    print("Test images created successfully")

if __name__ == "__main__":
    main()
