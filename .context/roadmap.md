# Project Roadmap

## Current Status

- ✅ Basic GUI implemented with PyQt
- ✅ Vision processing using LM Studio integration
- ✅ TMDB movie data lookup
- ✅ Debug visualization and logging
- ✅ Results view with confidence scores
- ✅ Auto-save functionality

## In Progress

- 🔄 Image preprocessing improvements
  - [ ] Adaptive contrast enhancement
  - [ ] Color masking for better text extraction
  - [ ] Dynamic scaling based on input size
- 🔄 OCR accuracy enhancements
  - [ ] Better handling of cursive fonts
  - [ ] Multiple pass verification
  - [ ] Context-aware text cleaning

## Next Steps

### Short Term
1. Add batch processing capability
   - Multiple image selection
   - Progress tracking
   - Bulk export options

2. Enhance error handling
   - Better error messages
   - Automatic retry logic
   - Recovery suggestions

3. Improve UX
   - Drag-and-drop support
   - Preview enhancements
   - Status indicators

### Medium Term
1. Camera integration
   - Real-time preview
   - Auto-capture
   - Image quality checks

2. Data management
   - Local database
   - Search functionality
   - Export formats (CSV, JSON, XML)

3. Results enhancement
   - Additional movie metadata
   - Cover art matching
   - Genre detection

### Long Term
1. Integration options
   - Media server plugins (Plex, Kodi)
   - Cloud storage sync
   - API endpoints

2. Advanced features
   - Barcode scanning
   - Cover art generation
   - Machine learning improvements

3. Platform expansion
   - Web interface
   - Mobile app
   - Network scanning

## Technical Debt

1. Test coverage
   - [ ] Integration tests
   - [ ] UI tests
   - [ ] Performance benchmarks

2. Code quality
   - [ ] Type hints completion
   - [ ] Documentation updates
   - [ ] Code organization

3. Dependencies
   - [ ] Version updates
   - [ ] Security audit
   - [ ] Performance optimization

## Known Issues

1. Vision Processing
   - Variable accuracy with cursive fonts
   - Slow processing of large images
   - Memory usage with batch processing

2. User Interface
   - Limited keyboard shortcuts
   - No progress indication for long operations
   - Settings management needs improvement

3. Integration
   - LM Studio connection handling
   - TMDB rate limiting
   - Error recovery
