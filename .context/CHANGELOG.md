# Changelog

## [Unreleased]

### Changed
- Improved vision processing confidence calculation:
  - Added progressive word count penalty for long titles
  - Removed capitalization boost for long titles
  - Enhanced title length validation
  - Added additional confidence modifiers
- Updated preprocessing pipeline:
  - Added adaptive image sizing
  - Optimized CLAHE parameters
  - Enhanced text clarity with morphological operations
- Added comprehensive integration tests for vision processing
- Added detailed documentation for vision processing system

### Added
- New integration test suite (test_vision_integration.py)
- Vision processing documentation (vision_processing.md)
- Advanced confidence scoring system
- Progressive penalties for long titles

### Fixed
- Title confidence calculation for long titles
- Preprocessing pipeline optimization
- Integration with GUI confidence display

## [1.0.0] - 2024-02-28
### Added
- Initial release with basic VHS cover text extraction
- LM Studio integration
- GUI interface
- Basic preprocessing pipeline
