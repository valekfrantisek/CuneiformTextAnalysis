document.addEventListener('DOMContentLoaded', () => {
    const analyzeButton = document.getElementById('analyze-button');
    const uploadButton = document.getElementById('upload-button');
    const inputText = document.getElementById('input-text');
    const fileUpload = document.getElementById('file-upload');
    const output = document.getElementById('basic-output');
    const layoutOptions = document.querySelectorAll('.layout-option');
    const SERVER_URL = 'http://127.0.0.1:5000';

    // analyzeButton.addEventListener('click', analyzeText);
    uploadButton.addEventListener('click', (event) => {
        event.preventDefault();
        uploadFile();
    });

    layoutOptions.forEach(option => {
        option.addEventListener('click', () => {
            layoutOptions.forEach(opt => opt.classList.remove('selected'));
            option.classList.add('selected');
        });
    });

    function getSelectedLayout() {
        const selectedOption = document.querySelector('.layout-option.selected');
        return selectedOption ? selectedOption.dataset.layout : 'default';
    }

    async function uploadFile() {    
        const file = fileUpload.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('layout', getSelectedLayout());
    
            const maxRetries = 3;
            for (let attempt = 0; attempt < maxRetries; attempt++) {
                try {
                    console.log(`Attempt ${attempt + 1} of ${maxRetries}`);
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
    
                    const response = await fetch(`${SERVER_URL}/upload`, {
                        method: 'POST',
                        body: formData,
                        signal: controller.signal
                    });
    
                    clearTimeout(timeoutId);
    
                    console.log('Response received. Status:', response.status);
                    console.log('Response headers:', response.headers);
    
                    if (response.ok) {
                        console.log('Starting to read response body...');
                        const text = await response.text();
                        console.log('Full response received. Size:', text.length);
                        console.log('Parsing JSON...');
                        const jsonResult = JSON.parse(text);
                        console.log('JSON parsed successfully.');
                        output.textContent = JSON.stringify(jsonResult, null, 2);
                        return; // Success, exit the function
                    } else {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                } catch (error) {
                    console.error(`Attempt ${attempt + 1} failed:`, error);
                    if (attempt === maxRetries - 1) {
                        output.textContent = 'Error processing the file after multiple attempts: ' + error.message;
                    }
                }
            }
        } else {
            output.textContent = 'Please select a file first.';
        }
    }

    // Prevent navigation
    window.onbeforeunload = function() {
        return "Are you sure you want to leave? Your upload may be interrupted.";
    };

    // async function analyzeText() {
    //     const text = inputText.value;
    //     if (text) {
    //         try {
    //             const response = await fetch(`${SERVER_URL}/analyze`, { 
    //                 method: 'POST',
    //                 headers: {
    //                     'Content-Type': 'application/json',
    //                 },
    //                 body: JSON.stringify({ text }),
    //             });
    //             const result = await response.json();
    //             output.textContent = JSON.stringify(result, null, 2);
    //         } catch (error) {
    //             output.textContent = 'Error analyzing the text: ' + error.message;
    //             console.error('Error:', error);
    //         }
    //     } else {
    //         output.textContent = 'Please enter text for analysis.';
    //     }
    // }
});