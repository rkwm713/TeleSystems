# Katapult JSON Processor

This module provides functionality for processing Katapult JSON exports and generating Excel-based make ready reports.

## Overview

The processor handles complex Katapult JSON structures containing poles, connections, and attachments, extracting relevant data for make-ready reports.

## Key Components

- **core.py**: Main processing functions and data flow coordination
- **data_extraction.py**: Functions to extract data from various parts of the JSON structure
- **node_processing.py**: Pole/node specific processing functions
- **connection_processing.py**: Functions for working with connections and spans
- **movement_processing.py**: Generation of movement summaries and remedy descriptions
- **height_utils.py**: Utilities for working with height measurements
- **utils.py**: General utility functions
- **excel_generator.py**: Excel report creation and formatting
- **constants.py**: Shared constants and configuration values

## Features

### Pole Data Extraction
- Comprehensive pole tag, SCID, and location extraction
- Improved pole structure extraction (height, class, species)
- Construction grade determination from pole class
- Proposed riser and guy detection

### Connection Analysis
- Span length calculation
- Lowest height determination for telecommunications and electrical
- Midspan height calculation and analysis
- Connection type classification

### Attacher Processing
- Extraction of attacher heights and proposed changes
- Down guy detection and processing
- Reference span analysis with directional information
- Backspan analysis and bearing calculation

### Movement Processing
- Detailed movement summaries for all attachers
- Comprehensive remedy descriptions for proposed attachments
- Intelligent underground connection detection
- Proposed attachment height formatting

### Excel Report Generation
- Professional Excel report with proper formatting
- Summary statistics sheet
- Extended attachment and movement information
- Midspan height reporting
