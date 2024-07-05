document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-upload');
    const fileNameDisplay = document.getElementById('file-name');
    const output = document.getElementById('basic-output');
    const errors = document.getElementById('error-output')
    const layoutOptions = document.querySelectorAll('.layout-option');
    const SERVER_URL = 'http://127.0.0.1:5000';
    const analyzeButtonSigns = document.getElementById('analyze-button-signs');
    const analyzeButtonWords = document.getElementById('analyze-button-words');
    const analyzeButtonGlossary = document.getElementById('analyze-button-glossary');
    const analyzeButtonORACC = document.getElementById('analyze-button-oracc');
    const downloadButtonCSV = document.getElementById('download-button-csv');
    const downloadButtonEXCEL = document.getElementById('download-button-excel');
    let currentUploadId = null;
    let layout = 'lines'

    analyzeButtonSigns.disabled = true;
    analyzeButtonWords.disabled = true;
    analyzeButtonGlossary.disabled = true;
    analyzeButtonORACC.disabled = true;
    downloadButtonCSV.disabled = true
    downloadButtonEXCEL.disabled = true

    dropZone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('dragover');
    }

    function unhighlight(e) {
        dropZone.classList.remove('dragover');
    }

    dropZone.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', handleFiles);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files instanceof FileList && files.length > 0) {
            uploadFile(files[0]);
        } else if (files.target && files.target.files && files.target.files.length > 0) {
            uploadFile(files.target.files[0]);
        }
    }

    dropZone.addEventListener('dragenter', (e) => {
        console.log('File dragged over drop zone');
    });
    
    dropZone.addEventListener('drop', (e) => {
        console.log('File dropped');
    });
    
    fileInput.addEventListener('change', (e) => {
        console.log('File selected via input');
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

    async function uploadFile(file) {    
        layout = getSelectedLayout()
        console.log(`Selected layout: ${layout}`);

        if (file) {
            const formData = new FormData();
            formData.append('file', file);

            fileNameDisplay.textContent = `Uploading file: ${file.name}`;
    
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
                        fileNameDisplay.textContent = `File uploaded: ${file.name}`;
                        return; // Success, exit the function
                    } else {
                        fileNameDisplay.textContent = `Error while uploading file: ${file.name}`;
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                } catch (error) {
                    console.error(`Attempt ${attempt + 1} failed:`, error);
                    if (attempt === maxRetries - 1) {
                        fileNameDisplay.textContent = `Error while uploading file: ${file.name}`;
                        output.textContent = 'Error processing the file after multiple attempts: ' + error.message;
                    }
                }
            }
        } else {
            output.textContent = 'Please select a file first.';
        }
    }

    function renderTable(data) {
        let tableHTML = '<table><tr><th>Sign</th><th>Preserved</th><th>Partial</th><th>Reconstructed</th><th>In &lt;&gt;</th><th>In ()</th><th>In &lt;&lt;&gt;&gt;</th></tr>';
        
        for (let sign in data) {
            tableHTML += `<tr>
                <td>${sign}</td>
                <td>${data[sign].preserved}</td>
                <td>${data[sign].partial}</td>
                <td>${data[sign].reconstructed}</td>
                <td>${data[sign]['in <>']}</td>
                <td>${data[sign]['in ()']}</td>
                <td>${data[sign]['in <<>>']}</td>
            </tr>`;
        }
        
        tableHTML += '</table>';
        return tableHTML;
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
            
            const signs_results = await response.text();
            console.log('Full response received. Size:', signs_results.length);
            console.log('Parsing JSON...');
            const jsonResult = JSON.parse(signs_results);
            console.log('JSON parsed successfully.');

            const tableHTML = renderTable(jsonResult.analysis);
            document.getElementById('basic-output').innerHTML = tableHTML;

            errors.textContent = `${JSON.stringify(jsonResult.syntax_errors)}`;

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