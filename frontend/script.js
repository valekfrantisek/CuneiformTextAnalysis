document.addEventListener('DOMContentLoaded', () => {
    const uploadButton = document.getElementById('upload-button');
    const fileUpload = document.getElementById('file-upload');
    const uploadInfo = document.getElementById('upload-info');
    const output = document.getElementById('basic-output');
    const layoutOptions = document.querySelectorAll('.layout-option');
    const SERVER_URL = 'http://127.0.0.1:5000';
    const analyzeButtonSigns = document.getElementById('analyze-button-signs');
    const analyzeButtonWords = document.getElementById('analyze-button-words');
    const analyzeButtonGlossary = document.getElementById('analyze-button-glossary');
    const analyzeButtonORACC = document.getElementById('analyze-button-oracc');
    let currentUploadId = null;
    let layout = 'lines'

    analyzeButtonSigns.disabled = true;
    analyzeButtonWords.disabled = true;
    analyzeButtonGlossary.disabled = true;
    analyzeButtonORACC.disabled = true;

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

    analyzeButtonSigns.addEventListener('click', (event) => {
        event.preventDefault();
        analyzeSigns();
    });

    analyzeButtonWords.addEventListener('click', (event) => {
        event.preventDefault();
        analyzeWords();
    });

    analyzeButtonGlossary.addEventListener('click', (event) => {
        event.preventDefault();
        analyzeGlossary();
    });

    analyzeButtonORACC.addEventListener('click', (event) => {
        event.preventDefault();
        analyzeORACC();
    });

    function getSelectedLayout() {
        const selectedOption = document.querySelector('.layout-option.selected');
        return selectedOption ? selectedOption.dataset.layout : 'lines';
    }

    async function uploadFile() {    
        const file = fileUpload.files[0];
        layout = getSelectedLayout()
        console.log(`Selected layout: ${layout}`);

        if (file) {
            const formData = new FormData();
            formData.append('file', file);
    
            const maxRetries = 3;
            for (let attempt = 0; attempt < maxRetries; attempt++) {
                try {
                    console.log(`Attempt ${attempt + 1} of ${maxRetries}`);
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
    
                    const response = await fetch(`${SERVER_URL}/upload/${layout}`, {
                        method: 'POST',
                        body: formData,
                        signal: controller.signal,
                        credentials: 'include'
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
                        currentUploadId = jsonResult.upload_id;
                        analyzeButtonSigns.disabled = false;
                        analyzeButtonWords.disabled = false;
                        analyzeButtonGlossary.disabled = false;
                        analyzeButtonORACC.disabled = false;
                        uploadInfo.textContent = `File uploaded: ${jsonResult.filename}`;
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

    async function analyzeSigns() {
        console.log('Analyzing signs');

        if (!currentUploadId) {
            output.textContent = 'Please upload a file first.';
            return;
        }
        try {
            const response = await fetch(`${SERVER_URL}/analyzeSignsAction/${currentUploadId}`, {
                method: 'POST',
                });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            output.textContent = `Processing result: ${JSON.stringify(result, null, 2)}`;
        } catch (error) {
            console.error('Error:', error);
            output.textContent = `Error_catch: ${error.message}`;
        }
    }

    async function analyzeWords() {
        console.log('Analyzing words');
        try {
            const response = await fetch(`${SERVER_URL}/analyzeWordsAction`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ data: 'Some data' }) // Můžete upravit odesílaná data podle potřeby
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            output.textContent = `Result: ${JSON.stringify(result)}`;
        } catch (error) {
            console.error('Error:', error);
            output.textContent = `Error: ${error.message}`;
        }
    } 

    async function analyzeGlossary() {
        console.log('Analyzing glossary');
        try {
            const response = await fetch(`${SERVER_URL}/analyzeGlossaryAction`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ data: 'Some data' }) // Můžete upravit odesílaná data podle potřeby
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            output.textContent = `Result: ${JSON.stringify(result)}`;
        } catch (error) {
            console.error('Error:', error);
            output.textContent = `Error: ${error.message}`;
        }
    } 

    async function analyzeORACC() {
        try {
            const response = await fetch(`${SERVER_URL}/analyzeORACCAction`, {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            output.textContent = `Result: ${JSON.stringify(result)}`;
        } catch (error) {
            console.error('Error:', error);
            output.textContent = `Error: ${error.message}`;
        }
    } 

    // Prevent navigation
    // window.onbeforeunload = function() {
    //     return "Are you sure you want to leave? Your analysis may be interrupted.";
    // };
});