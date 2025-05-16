# HTML Templates

This directory contains HTML templates used by the Flask web application for the Make-Ready Report Generator. These templates are rendered by Flask, typically by passing data from the Python backend to dynamically generate the HTML content served to the user's browser.

## Files

*   **`index.html`**:
    *   **Purpose**: This is the main landing page of the application.
    *   **Functionality**: It typically includes the form for users to upload their Katapult JSON (required) and SPIDAcalc JSON (optional) files. It may also contain input fields for user-selectable options, such as targeted pole selection or conflict resolution preferences.

*   **`result.html`**:
    *   **Purpose**: This template is used to display the results after the data processing is complete.
    *   **Functionality**: It will present a summary of the processing, provide a download link for the generated Make-Ready Excel report, and embed the interactive Leaflet.js map showing the processed pole locations and their statuses. It receives processed data from the Flask backend to populate these elements.

*   **`error.html`**:
    *   **Purpose**: This template is used to display error messages to the user if something goes wrong during file upload, data processing, or any other operation.
    *   **Functionality**: It provides a user-friendly way to communicate issues, such as invalid file formats, processing errors, or other exceptions.

## Templating Engine

These templates likely use Jinja2, the default templating engine for Flask. This allows for:
-   Embedding Python-like expressions and logic within the HTML.
-   Using template inheritance to maintain a consistent layout across pages.
-   Passing variables from the Flask backend to be displayed in the HTML.

## Interaction with Static Assets

These HTML templates will reference static assets (CSS and JavaScript) located in the `../static/` directory to control styling and client-side behavior. For example, `result.html` will include references to Leaflet.js library files and custom JavaScript for map initialization.
