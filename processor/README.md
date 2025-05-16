# Data Processor for Make-Ready Engineering

This `processor` package is the core engine of the Make-Ready Report Generator. It handles the complex task of ingesting, interpreting, and transforming data from Katapult JSON files (required) and SPIDAcalc JSON files (optional) to produce a comprehensive dataset ready for Excel report generation and map visualization.

## Overview

The processor is designed to:
- Parse and validate input JSON files.
- Normalize and match utility poles and attachments across potentially disparate data sources (Katapult and SPIDAcalc).
- Extract detailed information about poles, attachments (wires and equipment), and connections (spans).
- Perform necessary unit conversions (e.g., inches from Katapult, meters from SPIDAcalc to a consistent reporting unit like feet).
- Apply user-defined conflict resolution strategies when data from Katapult and SPIDAcalc differs.
- Determine the status of attachments (existing, new, modified, removed) by comparing different design scenarios (e.g., SPIDAcalc "Measured Design" vs. "Recommended Design").
- Calculate mid-span clearances and other relevant engineering data.
- Structure the processed data into a format suitable for generating the detailed Make-Ready Excel report.

## Key Modules and Responsibilities

-   **`core.py`**: Orchestrates the overall data processing workflow. Loads input data, manages the sequence of processing steps, and integrates outputs from other modules.
-   **`data_extraction.py`**: Contains functions specifically designed to extract relevant data fields from the nested structures of Katapult and SPIDAcalc JSON files.
-   **`node_processing.py`**: Focuses on processing pole-specific information, including attributes like height, class, species, owner, and location.
-   **`connection_processing.py`**: Handles data related to connections or spans between poles, including mid-span analysis and "from pole / to pole" lookups.
-   **`movement_processing.py`**: Determines attachment actions (Install, Remove, Existing, Modify) and generates summaries or labels for make-ready work, including height changes.
-   **`height_utils.py`**: Provides utilities for consistent handling and conversion of height measurements from different sources and units.
-   **`utils.py`**: A collection of general utility functions used across the processor, such as pole ID normalization, string manipulation, and safe data access.
-   **`excel_generator.py`**: Takes the fully processed data and generates the structured Make-Ready Excel report according to predefined formatting and column mappings.
-   **`constants.py`**: Defines shared constants, mappings (e.g., for attacher name normalization), and configuration values (e.g., conflict resolution strategies) to ensure consistency and maintainability.
-   **`__init__.py`**: Makes the `processor` directory a Python package.

## Core Processing Logic Highlights

### Data Ingestion and Validation
-   Loads Katapult JSON (required) and SPIDAcalc JSON (optional).
-   Performs basic validation of JSON structures.

### Pole Matching and Normalization
-   Normalizes pole identifiers from both Katapult (`PoleNumber`, `PL_number`, etc.) and SPIDAcalc (`locations[].label`) to create a canonical ID for matching.
-   Builds a list of poles to be processed, considering user-specified lists if provided (targeted pole selection).

### Per-Pole Processing Loop
For each pole:
-   **Pole-Level Data Extraction:** Gathers attributes like owner, height, class, species, PLA%, construction grade, and geographic coordinates from Katapult and/or SPIDAcalc.
-   **Unit Conversion:** Standardizes all measurements (especially heights) to a consistent unit.
-   **Attachment Consolidation:**
    -   Merges attachment data from Katapult (`photos[].wire[]`, `photos[].equipment[]`) and SPIDAcalc designs (`structure.wires`, `structure.equipments`).
    -   Applies conflict resolution rules for discrepancies in existing attachment heights or pole attributes based on user selection.
-   **Status Determination:** Identifies attachments as New, Existing, Removed, or Modified by comparing SPIDAcalc's "Measured Design" vs. "Recommended Design", or based on Katapult data if SPIDAcalc is not present.
-   **Per-Attachment Data Extraction:** For each attachment, extracts attacher name, description, existing height, and proposed height.
-   **Mid-Span Data Extraction:** Calculates lowest communication and electrical heights in spans connected to the pole, primarily using Katapult connection and section photo data.
-   **Action Summary Generation:** Creates labels like `(I)`, `(R)`, `(E)` and notes for movements (e.g., "Raise X ft").

### Output Preparation
-   Constructs a list of dictionaries, where each dictionary represents a row or a set of data points for the Excel report.

This structured approach ensures that data from potentially varied sources is processed consistently and accurately, leading to reliable Make-Ready reports.
