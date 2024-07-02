document.addEventListener('DOMContentLoaded', () => {
    const analyzeButton = document.getElementById('analyze-button');
    const uploadButton = document.getElementById('upload-button');
    const inputText = document.getElementById('input-text');
    const fileUpload = document.getElementById('file-upload');
    const output = document.getElementById('basic-output');
    const layoutOptions = document.querySelectorAll('.layout-option');
    const SERVER_URL = 'http://127.0.0.1:5000';

    analyzeButton.addEventListener('click', analyzeText);
    uploadButton.addEventListener('click', uploadFile);

    layoutOptions.forEach(option => {
        option.addEventListener('click', () => {
            layoutOptions.forEach(opt => opt.classList.remove('selected'));
            option.classList.add('selected');
        });
    });

    async function uploadFile() {
        const file = fileUpload.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('file', file);

            const selectedLayout = getSelectedLayout();
            formData.append('layout', selectedLayout);

            try {
                console.log('Attempting to upload file...');
                const response = await fetch(`${SERVER_URL}/upload`, {
                    method: 'POST',
                    body: formData,
                });
                console.log('Response status:', response.status);
                if (response.ok) {
                    const result = await response.json();
                    output.textContent = JSON.stringify(result, null, 2);
                    fileUpload.value = '';
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            } catch (error) {
                output.textContent = 'Error processing the file: ' + error.message;
                console.error('Error:', error);
            }
        } else {
            output.textContent = 'Please select a file first.';
        }
    }

    function getSelectedLayout() {
        const selectedOption = document.querySelector('.layout-option.selected');
        return selectedOption ? selectedOption.dataset.layout : 'default';
    }

    async function analyzeText() {
        const text = inputText.value;
        if (text) {
            try {
                const response = await fetch(`${SERVER_URL}/analyze`, { 
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text }),
                });
                const result = await response.json();
                output.textContent = JSON.stringify(result, null, 2);
            } catch (error) {
                output.textContent = 'Error analyzing the text: ' + error.message;
                console.error('Error:', error);
            }
        } else {
            output.textContent = 'Please enter text for analysis.';
        }
    }
});