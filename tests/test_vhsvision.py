"""
Tests for VHSVision class with enhanced preprocessing and OCR.
"""
import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch, ANY

from src.vision.vhs_vision import VHSVision, APIError

@pytest.fixture
def mock_api_response():
    """Mock successful API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "Test Movie Title"
                }
            }
        ]
    }

@pytest.fixture
def mock_preprocessor():
    """Mock preprocessor with configurable behavior."""
    mock = Mock()
    mock.preprocess.return_value = np.zeros((100, 100), dtype=np.uint8)
    mock.estimate_text_clarity.return_value = 30.0
    mock.extract_regions.return_value = [
        Mock(image=np.zeros((50, 50)), width=50, height=50)
    ]
    mock.compute_region_score.return_value = 0.85
    return mock

@pytest.fixture
def vhs_vision(mock_preprocessor, mock_api_response):
    """VHSVision instance with mocked dependencies."""
    with patch('src.vision.vhs_vision.PreprocessingPipeline', return_value=mock_preprocessor), \
         patch.object(VHSVision, '_make_api_request', return_value=mock_api_response):
        vision = VHSVision(save_debug=True)
        vision.scorer = Mock()
        vision.scorer.score_text.return_value = 75.0
        return vision

def test_preprocessing_retry_on_low_clarity(mock_preprocessor, vhs_vision, mock_api_response):
    """Test preprocessing retry logic for low clarity images."""
    # Setup
    mock_preprocessor.estimate_text_clarity.side_effect = [15.0, 28.0]  # First low, then better
    image = np.zeros((200, 200), dtype=np.uint8)
    
    # Execute
    with patch.object(vhs_vision, '_make_api_request', return_value=mock_api_response):
        result = vhs_vision.extract_info(image, "title")
    
    # Verify
    assert mock_preprocessor.preprocess.call_count == 2
    assert mock_preprocessor.preprocess.call_args_list[1][1] == {
        'clahe_clip_limit': 3.0,
        'bilateral_sigma_color': 15,
        'sharpening_strength': 1.2
    }
    assert result["validated"] is True

def test_confidence_weighted_scoring(mock_preprocessor, vhs_vision, mock_api_response):
    """Test confidence scoring with region quality weighting."""
    # Setup
    mock_preprocessor.compute_region_score.return_value = 0.9
    vhs_vision.scorer.score_text.return_value = 80.0
    image = np.zeros((200, 200), dtype=np.uint8)
    
    # Execute
    with patch.object(vhs_vision, '_make_api_request', return_value=mock_api_response):
        result = vhs_vision.extract_info(image, "title")
    
    # Verify weighted confidence calculation
    expected_confidence = 80.0 * (0.7 + 0.3 * 0.9)  # Base formula
    assert abs(result["confidence"] - expected_confidence) < 0.1
    assert result["region_score"] == 0.9

@pytest.mark.parametrize("category,expected_prompt", [
    ("title", "High confidence text region. Extract movie title from this enhanced VHS cover image."),
    ("year", "High confidence text region. Find the release year from this enhanced VHS cover image."),
])
def test_category_specific_prompts(mock_preprocessor, vhs_vision, mock_api_response, category, expected_prompt):
    """Test category-specific prompt generation."""
    # Setup
    mock_preprocessor.compute_region_score.return_value = 0.9
    image = np.zeros((200, 200), dtype=np.uint8)
    
    with patch.object(vhs_vision, '_process_region') as mock_process:
        # Execute
        with patch.object(vhs_vision, '_make_api_request', return_value=mock_api_response):
            vhs_vision.extract_info(image, category)
        
        # Verify prompt contains expected text
        called_prompt = mock_process.call_args[0][1]
        assert expected_prompt in called_prompt

def test_tesseract_fallback(mock_preprocessor, vhs_vision, mock_api_response):
    """Test Tesseract OCR fallback for low confidence results."""
    # Setup
    # Make API return low confidence result
    vhs_vision.scorer.score_text.side_effect = [30.0, 60.0]  # LM Studio low, Tesseract better
    image = np.zeros((200, 200), dtype=np.uint8)
    
    with patch('pytesseract.image_to_string', return_value="Test Movie Title"), \
         patch.object(vhs_vision, '_make_api_request', return_value=mock_api_response):
        # Execute
        result = vhs_vision.extract_info(image, "title")
        
        # Verify
        assert result["confidence"] == 60.0
        assert result["text"] == "Test Movie Title"
        assert result["source"] == "tesseract"

def test_error_handling_on_api_failure(mock_preprocessor, vhs_vision):
    """Test error handling when API fails."""
    # Setup
    image = np.zeros((200, 200), dtype=np.uint8)
    
    with patch.object(vhs_vision, '_process_region', side_effect=APIError("API Error")):
        # Execute
        result = vhs_vision.extract_info(image, "title")
        
        # Verify
        assert result["validated"] is False
        assert result["confidence"] == 0.0
        assert "error" in result

def test_timeout_handling(mock_preprocessor, vhs_vision):
    """Test timeout handling during processing."""
    # Setup
    image = np.zeros((200, 200), dtype=np.uint8)
    
    with patch.object(vhs_vision, '_process_region') as mock_process:
        mock_process.side_effect = TimeoutError("Processing timed out")
        
        # Execute
        result = vhs_vision.extract_info(image, "title", timeout=1)
        
        # Verify
        assert result["validated"] is False
        assert "error" in result
        assert "Processing timed out" in result["error"]  # Match exact error message
