# Project Context

## Overview
The Media Processor is a specialized application designed to streamline the process of creating eBay listings for physical media (VHS tapes, DVDs, CDs, vinyl records, cassette tapes). It uses advanced image processing and OCR to extract key information from media covers and labels.

## Current Status

### Core Features Implemented
1. **Image Processing Pipeline**
   - Advanced VisionProcessor with multi-stage processing
   - Ollama Vision integration for text extraction
   - Region of Interest (ROI) detection for different media regions
   - Debug image output for regions

2. **Basic GUI Framework**
   - Modern Flet-based interface
   - File selection and preview
   - Basic image processing workflow
   - Results display

### Critical Gaps
1. **eBay Integration**
   - No API connection to eBay
   - Missing listing creation functionality
   - No template management for different media types

2. **Media Processing**
   - OCR challenges with VHS covers:
     - Low confidence in text detection
     - Issues with complex backgrounds
     - Struggles with varying text styles
   - No media type detection
   - Missing barcode/UPC scanning
   - No metadata enrichment from external APIs

3. **User Experience**
   - Basic error handling
   - No progress indicators
   - Limited feedback during processing
   - No batch processing capability
   - No settings/configuration UI

4. **Data Management**
   - No local database integration
   - No history/tracking of processed items
   - No export functionality
   - No backup/restore features

## Technical Progress
1. **Vision Processing Improvements**
   - Implemented Ollama Vision integration:
     - Local LLM-based text extraction using MiniCPM-o-2_6
     - Optimized region-specific prompting
     - Smart confidence estimation for each region type
     - Debug image output for visual verification
   - Simplified image processing pipeline
   - Created comprehensive testing framework
   - See detailed analysis in ocr_challenges.md

2. **Next Steps**
   - Fine-tune region coordinates for optimal text capture
   - Optimize prompts for better response accuracy
   - Add response validation and error handling
   - Integrate vision processor with main pipeline
   - Add automated model verification and fallback options

3. **Code Organization**
   - Incomplete documentation
   - Limited test coverage
   - Missing type hints in some modules
   - No logging system

2. **Development Infrastructure**
   - No CI/CD pipeline
   - Limited automated testing
   - No performance benchmarks
   - Inconsistent error handling
