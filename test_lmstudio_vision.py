"""
Test VHS cover vision implementation using LM Studio.
"""
import cv2
import json
import numpy as np
from datetime import datetime
from src.vision.lmstudio_vision import VHSVision
from typing import Dict, List, Tuple
import os
import time
import argparse

def process_vhs_image(
    vision: VHSVision,
    image: np.ndarray
) -> Dict[str, Dict]:
    """Process VHS cover image using LM Studio vision model to extract title, year, and runtime."""
    results = {}
    info_types = ["title", "year", "runtime"]
    
    for info_type in info_types:
        print(f"\nExtracting {info_type} from VHS cover...")
        
        # Process image and measure time
        start_time = time.time()
        result = vision.extract_info(image, info_type=info_type)
        end_time = time.time()
        
        processing_time = end_time - start_time
        results[info_type] = result
        
        # Print results
        print(f"\nMethod: {result['method']}")
        print(f"Text: {result['text']}")
        print(f"Confidence: {result['confidence']:.1f}%")
        print(f"Processing Time: {processing_time:.2f} seconds")
        
        # Show if confidence meets threshold
        threshold_met = vision.is_high_confidence(result)
        print(f"Confidence Threshold Met: {threshold_met}")
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        
        print("-" * 40)
    
    return results

def main():
    """Test VHS cover text extraction using LM Studio."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test VHS cover text extraction")
    parser.add_argument("--image", default="testvhs.jpg",
                      help="Path to VHS cover image to process")
    args = parser.parse_args()
    
    print("\nInitializing VHS Vision with LM Studio...")
    vision = VHSVision()  # Let it auto-detect the current model
    
    # Ensure debug output directory exists
    if not os.path.exists('debug_output'):
        os.makedirs('debug_output')
    
    print("\nLoading test image...")
    image = cv2.imread(args.image)
    if image is None:
        print(f"Failed to load test image: {args.image}")
        return
        
    # Print image details
    print(f"Image dimensions: {image.shape}")
    print(f"Image type: {image.dtype}")
    if image.size == 0:
        print("Warning: Image is empty")
        return

    # Save original for reference
    cv2.imwrite('debug_output/original_full.jpg', image)
    
    # Process image
    results = process_vhs_image(vision, image)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'vision_results_{timestamp}.json'
    
    # Remove raw response from results to keep JSON clean
    clean_results = {}
    for region, data in results.items():
        clean_results[region] = {
            k: v for k, v in data.items() 
            if k != 'raw_response'
        }
    
    with open(output_file, 'w') as f:
        json.dump(clean_results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    print("\nDebug images saved with timestamp")
    print("\nNote: Make sure LM Studio is running and configured with:")
    print("Endpoint: http://127.0.0.1:1234")
    print(f"Model: {vision.model}")

if __name__ == "__main__":
    main()
