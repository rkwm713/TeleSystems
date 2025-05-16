# Static Assets

This directory contains static files used by the frontend of the Make-Ready Report Generator web application. These files are served directly to the user's browser and are essential for the presentation and client-side functionality of the interface.

## Directory Structure

*   **`css/`**: Contains Cascading Style Sheets (CSS) files.
    *   `styles.css`: Main stylesheet for the application, defining the visual appearance of HTML elements, layout, and overall look and feel.
*   **`js/`**: Contains JavaScript files for client-side interactivity.
    *   `upload.js`: (Presumed) Handles client-side logic related to file uploads, form interactions, or dynamic updates on the upload page.
    *   `debug.js`: (Presumed) May contain JavaScript utilities or functions used for debugging purposes during development.
    *   *Map-related JavaScript*: Client-side JavaScript for initializing and interacting with the Leaflet.js map (e.g., adding markers, popups, handling map events) would also reside here or be linked from the HTML templates.
*   **`test-data/`**: Contains sample data files that can be used for testing the application's processing capabilities.
    *   `sample.json`: (Presumed) An example JSON file (likely Katapult or SPIDAcalc format) for testing purposes.

## Purpose

The files in this directory are responsible for:
-   **Styling**: Defining the visual presentation of the web pages.
-   **Client-Side Logic**: Enhancing user experience with interactive elements, form validation, dynamic content updates, and managing the interactive map.
-   **Testing**: Providing sample data to facilitate development and testing of the application's backend processing logic.

These assets are referenced by the HTML templates in the `../templates/` directory.
