import cv2
import numpy as np
from src.utils.opencv_utils import denoise_image

def test_denoising():
    # Create a noisy test image (100x100 grayscale)
    image = np.zeros((100, 100), dtype=np.uint8)
    cv2.rectangle(image, (20, 20), (80, 80), 255, -1)
    
    # Add noise
    noise = np.random.normal(0, 25, image.shape).astype(np.uint8)
    noisy = cv2.add(image, noise)
    
    # Apply denoising
    denoised = denoise_image(noisy)
    
    # Check ROI standard deviations
    roi_noisy = noisy[30:70, 30:70]
    roi_denoised = denoised[30:70, 30:70]
    
    print("Noisy ROI std: %.2f" % np.std(roi_noisy))
    print("Denoised ROI std: %.2f" % np.std(roi_denoised))
    print("Improvement: %.2f" % (np.std(roi_noisy) - np.std(roi_denoised)))
    
    # Display results
    cv2.imwrite("noisy.jpg", noisy)
    cv2.imwrite("denoised.jpg", denoised)

if __name__ == "__main__":
    test_denoising()
