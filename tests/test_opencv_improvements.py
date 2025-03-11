import os
import cv2
import numpy as np
import pytest
from src.utils.opencv_utils import (
    enhance_contrast,
    denoise_image,
    preprocess_image,
    estimate_text_clarity
)

@pytest.fixture
def sample_image():
    # Create a test directory if it doesn't exist
    test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    # Load test image
    image_path = os.path.join(test_dir, 'sample_vhs.jpg')
    if not os.path.exists(image_path):
        # Create synthetic test image with text if real image doesn't exist
        img = np.ones((300, 400), dtype=np.uint8) * 128
        cv2.putText(img, "TEST TEXT", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, 0, 3)
        cv2.imwrite(image_path, img)
    return cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

def test_contrast_enhancement(sample_image):
    enhanced = enhance_contrast(sample_image)
    
    # Verify enhanced contrast
    assert enhanced.dtype == np.uint8
    assert enhanced.shape == sample_image.shape
    
    # Check if contrast was improved
    orig_std = np.std(sample_image)
    enhanced_std = np.std(enhanced)
    assert enhanced_std >= orig_std * 0.8, "Contrast should be maintained or improved"
    
    # Verify text clarity was preserved or improved
    orig_clarity = estimate_text_clarity(sample_image)
    enhanced_clarity = estimate_text_clarity(enhanced)
    assert enhanced_clarity >= orig_clarity * 0.8, "Text clarity should not degrade significantly"

def test_denoising_preservation(sample_image):
    # Add synthetic noise
    noisy = sample_image + np.random.normal(0, 25, sample_image.shape).astype(np.uint8)
    denoised = denoise_image(noisy)
    
    # Verify noise reduction
    assert np.std(denoised) < np.std(noisy), "Should reduce noise"
    
    # Verify edge preservation
    edges_orig = cv2.Canny(sample_image, 100, 200)
    edges_denoised = cv2.Canny(denoised, 100, 200)
    edge_retention = np.sum(edges_denoised) / np.sum(edges_orig)
    assert edge_retention >= 0.7, "Should preserve at least 70% of edges"

def test_preprocessing_pipeline(sample_image):
    # Test complete preprocessing pipeline
    preprocessed = preprocess_image(sample_image)
    
    # Verify basic properties
    assert preprocessed.dtype == np.uint8
    assert len(preprocessed.shape) == 2  # Should be grayscale
    
    # Verify improved or maintained text clarity
    orig_clarity = estimate_text_clarity(sample_image)
    final_clarity = estimate_text_clarity(preprocessed)
    assert final_clarity >= orig_clarity * 0.8, "Text clarity should be maintained"
    
    # Check if extreme values are handled properly
    dark_image = (sample_image * 0.3).astype(np.uint8)
    bright_image = cv2.add(sample_image, 100)
    
    dark_processed = preprocess_image(dark_image)
    bright_processed = preprocess_image(bright_image)
    
    assert np.mean(dark_processed) > np.mean(dark_image), "Should improve dark images"
    assert np.std(bright_processed) >= np.std(bright_image) * 0.5, "Should maintain contrast in bright images"

def test_noise_adaptive_processing(sample_image):
    # Test noise adaptation
    noise_levels = [5, 15, 30]
    clarity_scores = []
    
    for noise_std in noise_levels:
        noisy = sample_image + np.random.normal(0, noise_std, sample_image.shape).astype(np.uint8)
        processed = preprocess_image(noisy)
        clarity_scores.append(estimate_text_clarity(processed))
    
    # Verify that clarity remains relatively stable across noise levels
    max_clarity = max(clarity_scores)
    min_clarity = min(clarity_scores)
    clarity_range = (max_clarity - min_clarity) / max_clarity
    
    assert clarity_range < 0.5, "Processing should be stable across noise levels"

def test_text_clarity_measure(sample_image):
    # Create degraded version
    blurred = cv2.GaussianBlur(sample_image, (7, 7), 0)
    
    # Test clarity measure
    orig_clarity = estimate_text_clarity(sample_image)
    blurred_clarity = estimate_text_clarity(blurred)
    
    assert orig_clarity > blurred_clarity, "Should detect reduced clarity in blurred image"
    assert orig_clarity > 0, "Should return positive clarity score for text"
