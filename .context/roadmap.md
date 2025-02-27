# Development Roadmap

## Recently Completed
- ✓ Optimized LM Studio connection management
  - Replaced continuous polling with manual refresh
  - Added connection status caching
  - Improved performance of status checks
  - Added visual loading indicator

## Current Sprint
- Fix TMDB integration
  - Resolve API key validation issues
  - Add error handling for failed API requests
  - Implement retry mechanism for temporary failures
- Improve OCR accuracy
  - Fine-tune image preprocessing parameters
  - Add additional debug visualization options
  - Implement confidence scoring for extracted text

## Future Improvements
- Batch processing capability
- Save/load processing configurations
- Enhanced metadata extraction
- Support for different media formats
- Automated testing improvements
- Export functionality enhancements

## Known Issues
- TMDB API key validation failing
- Some OCR accuracy challenges with certain tape labels
- Need to improve error handling for network issues
