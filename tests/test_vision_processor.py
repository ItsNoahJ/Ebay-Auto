"""
Tests for VHS tape image processing functionality.
"""
import os
import pytest
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from src.vision.processor import VisionProcessor

@pytest.fixture
def temp_image_dir(tmp_path):
    """Create a temporary directory for test images."""
    return tmp_path / "test_images"

@pytest.fixture
def vision_processor(temp_image_dir):
    """Create a vision processor instance for testing."""
    debug_dir = str(temp_image_dir / "debug")
    os.makedirs(debug_dir, exist_ok=True)
    return VisionProcessor(debug_output_dir=debug_dir)

def create_test_image(output_path: str, text: dict) -> str:
    """
    Create a test image with known text.
    
    Args:
        output_path: Path to save the test image
        text: Dictionary of text to write in each region
    """
    # Create base image
    width = 1600
    height = 1200
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Use a large font size for better OCR
    font_size = 72
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        try:
            # Try Windows system font as backup
            font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
    
    # Add text to image with precise positioning matching ROI regions
    draw.text((width * 0.02 + 20, height * 0.02 + 20), text.get('title', ''), fill='black', font=font)
    draw.text((width * 0.02 + 20, height * 0.25 + 20), text.get('year', ''), fill='black', font=font)
    draw.text((width * 0.65 + 20, height * 0.25 + 20), text.get('runtime', ''), fill='black', font=font)
    
    # Add a light border around text regions to improve contrast
    for region in ['title', 'year', 'runtime']:
        if text.get(region):
            bbox = draw.textbbox((0, 0), text[region], font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            if region == 'title':
                x = int(width * 0.02) + 20
                y = int(height * 0.02) + 20
            elif region == 'year':
                x = int(width * 0.02) + 20
                y = int(height * 0.25) + 20
            else:  # runtime
                x = int(width * 0.65) + 20
                y = int(height * 0.25) + 20
            
            # Draw rectangle slightly larger than text
            draw.rectangle(
                [x-5, y-5, x+text_width+5, y+text_height+5],
                outline='black',
                width=2
            )
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)
    return output_path

def test_vision_processor_initialization(vision_processor):
    """Test vision processor initialization."""
    assert vision_processor.confidence_threshold == 60
    assert "title" in vision_processor.roi_regions
    assert "year" in vision_processor.roi_regions
    assert "runtime" in vision_processor.roi_regions

def test_image_preprocessing(vision_processor, temp_image_dir):
    """Test image preprocessing steps."""
    # Create a simple test image
    test_path = str(temp_image_dir / "preprocess_test.jpg")
    test_text = {
        "title": "Test Movie",
        "year": "1999",
        "runtime": "120 min"
    }
    create_test_image(test_path, test_text)
    
    # Load and preprocess image
    image = cv2.imread(test_path)
    processed = vision_processor._preprocess_image(image)
    
    # Verify preprocessing output
    assert isinstance(processed, np.ndarray)
    assert len(processed.shape) == 2  # Should be grayscale
    assert processed.dtype == np.uint8

def test_text_extraction(vision_processor, temp_image_dir, capsys):
    """Test text extraction from different regions."""
    # Create test image with known text
    test_path = str(temp_image_dir / "extraction_test.jpg")
    test_text = {
        "title": "The Matrix",
        "year": "1999",
        "runtime": "136 min"
    }
    create_test_image(test_path, test_text)
    
    # Process image
    results = vision_processor.process_image(test_path)
    
    # Verify results structure
    assert "extracted_data" in results
    assert "debug_info" in results
    
    # Verify debug info
    debug_info = results["debug_info"]
    assert os.path.exists(debug_info["original_image"])
    assert os.path.exists(debug_info["processed_image"])
    assert "confidence_scores" in debug_info
    
    # Output debug information
    print("\nDebug Info:")
    print(f"Confidence Scores: {results['debug_info']['confidence_scores']}")
    print(f"Extracted Title: '{results['extracted_data']['title']}'")
    print(f"Extracted Year: '{results['extracted_data']['year']}'")
    print(f"Extracted Runtime: '{results['extracted_data']['runtime']}'")
    
    # Check if expected text was found (allowing for some OCR variance)
    extracted = results["extracted_data"]
    title_match = "Matrix" in extracted["title"] or "MATRIX" in extracted["title"].upper()
    year_match = "1999" in extracted["year"]
    runtime_match = "min" in extracted["runtime"].lower()
    
    # Output detailed assertion info
    if not title_match:
        print(f"\nTitle match failed. Expected 'Matrix', got: {extracted['title']}")
    if not year_match:
        print(f"\nYear match failed. Expected '1999', got: {extracted['year']}")
    if not runtime_match:
        print(f"\nRuntime match failed. Expected 'min', got: {extracted['runtime']}")
        
    assert title_match, "Title text not found"
    assert year_match, "Year text not found"
    assert runtime_match, "Runtime text not found"

def test_invalid_image_handling(vision_processor, temp_image_dir):
    """Test handling of invalid image paths."""
    invalid_path = str(temp_image_dir / "nonexistent.jpg")
    
    with pytest.raises(ValueError):
        vision_processor.process_image(invalid_path)

def test_results_validation(vision_processor, temp_image_dir, capsys):
    """Test validation of OCR results."""
    # Create test image with clear text
    test_path = str(temp_image_dir / "validation_test.jpg")
    test_text = {
        "title": "CLEAR TEST TITLE",
        "year": "2000",
        "runtime": "90 MIN"
    }
    create_test_image(test_path, test_text)
    
    # Process and validate results
    results = vision_processor.process_image(test_path)
    is_valid = vision_processor.validate_results(results)
    
    # Output debug information
    print("\nDebug Info:")
    print(f"Confidence Scores: {results['debug_info']['confidence_scores']}")
    for region, score in results["debug_info"]["confidence_scores"].items():
        print(f"{region}: {score} vs threshold {vision_processor.confidence_threshold}")
        
    # Results should be valid for clear text
    assert is_valid, "Results validation failed - check confidence scores"
    
    # Verify all confidence scores
    confidence_scores = results["debug_info"]["confidence_scores"]
    assert all(score > 0 for score in confidence_scores.values()), "Some confidence scores are 0"
