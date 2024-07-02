document.addEventListener('DOMContentLoaded', () => {
    const analyzeButton = document.getElementById('analyze-button');
    const inputText = document.getElementById('input-text');
    const fileUpload = document.getElementById('file-upload');
    const output = document.getElementById('output');

    analyzeButton.addEventListener('click', async () => {
        const text = inputText.value;
        if (text) {
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text }),
                });
                const result = await response.json();
                output.textContent = JSON.stringify(result, null, 2);
            } catch (error) {
                output.textContent = 'Error analyzing the text.';
                console.error('Error:', error);
            }
        } else {
            output.textContent = 'Please enter text for analysis.';
        }
    });

    fileUpload.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                output.textContent = JSON.stringify(result, null, 2);
            } catch (error) {
                output.textContent = 'Error processing the file.';
                console.error('Error:', error);
            }
        }
    });
});