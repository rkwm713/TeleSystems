/**
 * Utility functions for debugging the file upload process
 */

// Enable this to show the debug panel
const SHOW_DEBUG_PANEL = true;

// Function to append debug info to the debug panel
function appendDebugInfo(message) {
    const debugPanel = document.getElementById('debug-info');
    const debugContent = document.getElementById('debug-content');
    
    if (!debugPanel || !debugContent) return;
    
    if (SHOW_DEBUG_PANEL) {
        debugPanel.classList.remove('d-none');
    }
    
    const timestamp = new Date().toLocaleTimeString();
    const formattedMessage = `[${timestamp}] ${message}`;
    
    debugContent.textContent = debugContent.textContent 
        ? debugContent.textContent + '\n' + formattedMessage 
        : formattedMessage;
}

// Function to check form validity
function checkFormValidity() {
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('json_file');
    
    if (!form || !fileInput) return false;
    
    let isValid = true;
    let validityDetails = [];
    
    // Check if form has correct enctype
    const enctype = form.getAttribute('enctype');
    validityDetails.push(`Form enctype: ${enctype}`);
    if (enctype !== 'multipart/form-data') {
        isValid = false;
        validityDetails.push('ERROR: Form enctype is not multipart/form-data');
    }
    
    // Check file input
    validityDetails.push(`File input exists: ${!!fileInput}`);
    validityDetails.push(`File input name: ${fileInput.name}`);
    
    // Check if file is selected
    const fileSelected = fileInput.files && fileInput.files.length > 0;
    validityDetails.push(`File selected: ${fileSelected}`);
    
    if (fileSelected) {
        const file = fileInput.files[0];
        validityDetails.push(`File name: ${file.name}`);
        validityDetails.push(`File type: ${file.type}`);
        validityDetails.push(`File size: ${file.size} bytes`);
    } else {
        isValid = false;
        validityDetails.push('ERROR: No file selected');
    }
    
    appendDebugInfo('Form validity check: ' + (isValid ? 'PASSED' : 'FAILED'));
    validityDetails.forEach(detail => appendDebugInfo('  ' + detail));
    
    return isValid;
}

// Test the file upload without submitting
function testFileUpload() {
    appendDebugInfo('Testing file upload...');
    
    // Check if the form is valid
    const isValid = checkFormValidity();
    
    // Create test FormData
    const form = document.getElementById('upload-form');
    if (!form) {
        appendDebugInfo('ERROR: Form not found');
        return;
    }
    
    const formData = new FormData(form);
    let formContents = {};
    
    for (let pair of formData.entries()) {
        if (pair[0] === 'json_file') {
            formContents[pair[0]] = pair[1].name; // Just log the filename
        } else {
            formContents[pair[0]] = pair[1];
        }
    }
    
    appendDebugInfo('Form data contents: ' + JSON.stringify(formContents));
    
    if (!formContents['json_file']) {
        appendDebugInfo('ERROR: json_file not present in FormData');
    }
    
    appendDebugInfo('Test result: ' + (isValid ? 'OK' : 'FAILED'));
}

// Add this to window for console access
window.debugUpload = {
    testUpload: testFileUpload,
    checkValidity: checkFormValidity,
    log: appendDebugInfo
};

document.addEventListener('DOMContentLoaded', function() {
    // Add a debug button if debugging is enabled
    if (SHOW_DEBUG_PANEL) {
        const form = document.getElementById('upload-form');
        const submitBtn = document.getElementById('submit-btn');
        
        if (form && submitBtn) {
            const debugBtn = document.createElement('button');
            debugBtn.type = 'button';
            debugBtn.className = 'btn btn-info mt-2';
            debugBtn.textContent = 'Test Upload';
            debugBtn.onclick = testFileUpload;
            
            submitBtn.parentNode.appendChild(debugBtn);
            
            appendDebugInfo('Debug mode enabled');
        }
    }
});
