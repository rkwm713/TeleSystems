# Make-Ready Report Generator

## Overview

The Make-Ready Report Generator is a Python-based web application designed to process utility pole data from Katapult and SPIDAcalc JSON files. It automates the generation of detailed Make-Ready Engineering Excel reports and provides an interactive map visualization of the processed poles. This tool aims to streamline the workflow for engineers and planners involved in utility infrastructure projects.

## Key Features

*   **Dual JSON Input:** Processes a required Katapult JSON file and an optional SPIDAcalc JSON file.
*   **Comprehensive Data Processing:** Extracts, normalizes, and consolidates data related to pole attributes, attachments, and mid-span information.
*   **Automated Excel Report Generation:** Creates a structured Excel report detailing existing conditions, proposed make-ready work, and engineering data for each pole.
*   **Interactive Map Visualization:** Displays processed poles on a Leaflet.js map within the web interface, showing pole locations and status summaries.
*   **Targeted Pole Selection:** Allows users to specify a list of pole numbers for focused processing.
*   **Conflict Resolution:** Provides user-configurable strategies for resolving data discrepancies between Katapult and SPIDAcalc sources for attachment heights and pole attributes.
*   **Web-Based Interface:** Utilizes Flask for a user-friendly interface to upload input files and view results.

## Project Structure

```
.
├── app.py                      # Main Flask application file, entry point
├── requirements.txt            # Python package dependencies
├── final_code_output.py        # (Purpose to be clarified, likely main processing script or an output)
├── dummy_output.xlsx           # Example of an output Excel file
├── UPLOAD_FIX_README.md        # (Specific README, content might need review/integration)
│
├── .clinerules/                # Project-specific rules and guidelines for development
├── processor/                  # Core data processing logic
│   ├── core.py                 # Main data loading and orchestration
│   ├── data_extraction.py      # Modules for extracting data from JSONs
│   ├── excel_generator.py      # Logic for creating the Excel report
│   ├── utils.py                # Utility functions (e.g., normalization, conversions)
│   └── ...                     # Other processing modules
│
├── static/                     # Static assets for the web interface
│   ├── css/                    # CSS stylesheets
│   └── js/                     # Client-side JavaScript files
│
├── templates/                  # HTML templates for the Flask application
│   ├── index.html              # Main upload page
│   ├── result.html             # Page to display results and map
│   └── error.html              # Error display page
│
└── uploads/                    # Directory for user-uploaded files and generated reports
```

## Technologies Used

*   **Backend:** Python, Flask
*   **Data Processing:** openpyxl (for Excel generation)
*   **Frontend:** HTML, CSS, JavaScript, Leaflet.js (for maps)

## Setup and Usage

1.  **Prerequisites:**
    *   Python 3.x
    *   Git (for cloning, if applicable)

2.  **Installation:**
    ```bash
    # Clone the repository (if applicable)
    # git clone <repository_url>
    # cd <project_directory>

    # Create a virtual environment (recommended)
    python -m venv venv
    # Activate the virtual environment
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt
    ```

3.  **Running the Application:**
    ```bash
    python app.py
    ```
    The application will typically be accessible at `http://127.0.0.1:5000` in your web browser.

4.  **How to Use:**
    *   Open the application in your browser.
    *   Use the interface to upload your Katapult JSON file (required) and SPIDAcalc JSON file (optional).
    *   Select any processing options (e.g., targeted pole list, conflict resolution strategy).
    *   Submit the form to start processing.
    *   Results, including a link to the generated Excel report and an interactive map, will be displayed.

## Folders

*   **`.clinerules/`**: Contains specific rules and guidelines that direct the AI-assisted development for this project, focusing on features like targeted pole selection, conflict resolution, and map integration.
*   **`processor/`**: Houses all the Python modules responsible for the core logic of parsing input files, extracting relevant data, performing calculations and transformations, and generating the final Excel report.
*   **`project-docs/`**: Contains detailed documentation about the Katapult and SPIDAcalc JSON structures, the Excel report format, and other guiding documents for development and understanding the project.
*   **`static/`**: Stores static files served directly to the web browser, such as CSS for styling, JavaScript for client-side interactions (including map functionality), and potentially images or test data.
*   **`templates/`**: Contains HTML templates used by the Flask framework to render the web pages presented to the user (e.g., the upload form, results display).
*   **`uploads/`**: A directory used by the application to temporarily store uploaded JSON files and the generated Excel reports. This folder might be configured to be cleaned periodically or managed based on deployment strategy.

---

*This README provides a general overview. For more detailed information, refer to the documentation in the `project-docs/` folder and the README files within specific subdirectories.*
