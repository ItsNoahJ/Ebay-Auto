# Project Context

## Overview
VHS Tape Scanner application for digitizing and cataloging VHS tape collections using computer vision and AI.

## Components
- GUI interface (PyQt6-based)
- LM Studio integration for text extraction
- Image processing pipeline
- TMDB integration for metadata enrichment

## Recent Changes
- Optimized LM Studio connection handling
  - Faster status checks using ping-style requests
  - Cached model state to maintain accuracy
  - Reduced connection check timeouts
  - Added manual refresh capability
  - Removed continuous polling
- GUI improvements
  - Status indicator with visual feedback
  - Loading animation during processing
  - Manual connection refresh button

## Current Status
- Core functionality working
- Connection management optimized for better performance
- Debug output available for troubleshooting
- Need to resolve TMDB integration issues (invalid API key)
