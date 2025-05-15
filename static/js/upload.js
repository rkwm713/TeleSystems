/**
 * Enhanced file upload experience with drag-and-drop functionality
 * For Katapult Make Ready Report Generator
 */

document.addEventListener('DOMContentLoaded', function() {
    // Core elements
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('json_file');
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    const loadingSpinner = document.getElementById('loading-spinner');
    
    // Enhanced UI elements
    const dropArea = document.getElementById('drop-area');
    const fileDetails = document.getElementById('file-details');
    const selectedFilename = document.getElementById('selected-filename');
    const selectedFilesize = document.getElementById('selected-filesize');
    const removeFileBtn = document.getElementById('remove-file');
    const debugInfo = document.getElementById('debug-info');
    const debugContent = document.getElementById('debug-content');
    
    // Check if required elements exist
    if (!form || !fileInput || !submitBtn || !dropArea) {
        console.error('Required elements not found!');
        return;
    }
    
    // Format bytes to human-readable size
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    // Prevent defaults for drag events
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop area during drag
    function highlight() {
        dropArea.classList.add('dragover');
    }
    
    // Remove highlight on drop or drag leave
    function unhighlight() {
        dropArea.classList.remove('dragover');
    }
    
    // Handle dropped files
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            try {
                // Only process the first file if multiple are dropped
                fileInput.files = files;
                console.log("File attached via drag & drop:", fileInput.files[0].name);
                
                // Verify the file was attached properly
                if (fileInput.files.length === 0) {
                    console.error("Failed to attach file to input element");
                    throw new Error("File attachment failed");
                }
                
                updateFileDetails();
            } catch (err) {
                console.error("Error handling dropped file:", err);
                alert("There was an error attaching your file. Please try using the browse button instead.");
            }
        }
    }
    
    // Update file details when a file is selected
    function updateFileDetails() {
        const file = fileInput.files[0];
        
        if (file) {
            // Set file details
            selectedFilename.textContent = file.name;
            selectedFilesize.textContent = formatBytes(file.size);
            
            // Show file details section
            fileDetails.classList.remove('d-none');
            
            // Add a selected class to the drop area
            dropArea.classList.add('file-selected');
            
            // Enable submit button
            submitBtn.disabled = false;
            
            // Validate file size
            validateFileSize(file);
        } else {
            // Reset UI
            resetFileSelection();
        }
    }
    
    // Reset file selection UI
    function resetFileSelection() {
        // Clear file input
        fileInput.value = '';
        
        // Hide file details section
        fileDetails.classList.add('d-none');
        
        // Remove selected class from drop area
        dropArea.classList.remove('file-selected');
        
        // Disable submit button if no file is selected
        submitBtn.disabled = true;
    }
    
    // Validate file size
    function validateFileSize(file) {
        const maxSize = 50 * 1024 * 1024; // 50MB in bytes
        
        if (file.size > maxSize) {
            // Create alert
            const alertContainer = document.createElement('div');
            alertContainer.classList.add('alert', 'alert-danger', 'alert-dismissible', 'fade', 'show', 'mt-3');
            alertContainer.innerHTML = `
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                File is too large! Maximum size is 50MB.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            // Insert alert before file details
            form.insertBefore(alertContainer, fileDetails);
            
            // Reset file selection
            resetFileSelection();
        }
    }
    
    // Add drag and drop event listeners
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle file drop
    dropArea.addEventListener('drop', handleDrop, false);
    
    // Handle file selection via input
    fileInput.addEventListener('change', updateFileDetails);
    
    // Handle remove file button click
    removeFileBtn.addEventListener('click', resetFileSelection);
    
    // Helper function to show debug information
    function showDebugInfo(message, data = null) {
        let debugText = message;
        if (data) {
            if (typeof data === 'object') {
                debugText += "\n" + JSON.stringify(data, null, 2);
            } else {
                debugText += "\n" + data;
            }
        }
        
        debugContent.textContent = debugText;
        debugInfo.classList.remove('d-none');
    }
    
    // Form submission handling
    form.addEventListener('submit', function(e) {
        e.preventDefault(); // Prevent default form submission initially
        
        // Verify enctype is set correctly
        if (form.getAttribute('enctype') !== 'multipart/form-data') {
            console.error("Form enctype is not set to multipart/form-data");
            form.setAttribute('enctype', 'multipart/form-data');
        }
        
        // Double-check that a file is selected and properly attached
        if (!fileInput || fileInput.files.length === 0) {
            const errorMsg = "No file selected for upload";
            console.error(errorMsg);
            showDebugInfo("ERROR: " + errorMsg);
            alert("Please select a file before submitting");
            return false;
        }
        
        const fileDetails = {
            name: fileInput.files[0].name,
            size: fileInput.files[0].size,
            type: fileInput.files[0].type,
            inputName: fileInput.name
        };
        
        console.log("Submitting form with file:", fileDetails.name);
        console.log("File details:", fileDetails);
        
        // Log form details for debugging
        const formData = new FormData(form);
        let formContents = {};
        for (let pair of formData.entries()) {
            if (pair[0] === 'json_file') {
                formContents[pair[0]] = pair[1].name; // Just log the filename
            } else {
                formContents[pair[0]] = pair[1];
            }
        }
        
        console.log("Form data:", formContents);
        showDebugInfo("Uploading file", fileDetails);
        
        // Show loading state
        submitText.textContent = 'Processing...';
        loadingSpinner.classList.remove('d-none');
        
        // We'll submit the form directly without disabling all elements
        // This ensures the file input remains active during submission
        submitBtn.disabled = true;
        
        // Submit the form programmatically
        setTimeout(() => {
            form.submit();
        }, 100);
        
        // Handle long processing time
        window.processingTimeout = setTimeout(() => {
            if (submitBtn.disabled) {
                // Reset UI
                submitBtn.disabled = false;
                submitText.textContent = 'Generate Report';
                loadingSpinner.classList.add('d-none');
                form.classList.remove('processing');
                
                // Show message
                const alertContainer = document.createElement('div');
                alertContainer.classList.add('alert', 'alert-warning', 'alert-dismissible', 'fade', 'show', 'mt-3');
                alertContainer.innerHTML = `
                    <i class="bi bi-clock-history me-2"></i>
                    The processing is taking longer than expected. You can wait or try again.
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                
                form.insertBefore(alertContainer, form.firstChild);
            }
        }, 30000); // 30 seconds
        
        return false; // Prevent default form submission, we'll handle it manually
    });
    
    // Disable submit button initially if no file is selected
    if (!fileInput || fileInput.files.length === 0) {
        submitBtn.disabled = true;
    }
    
    // Add a manual file selection check
    dropArea.addEventListener('click', function(e) {
        // If the click is not on the browse button, also trigger the file input
        if (e.target !== document.querySelector('label[for="json_file"]') && 
            !e.target.closest('label[for="json_file"]')) {
            fileInput.click();
        }
    });
});
