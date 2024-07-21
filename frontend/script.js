document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    
    const fileInput = document.getElementById('file-upload');
    const fileNameDisplay = document.getElementById('file-name');
    
    const output = document.getElementById('basic-output');
    const errors = document.getElementById('error-output')
    
    const layoutOptions = document.querySelectorAll('.layout-option');

    const obverseReverseCheckbox = document.getElementById('ORACCObverseReverse');
    const columnsCheckbox = document.getElementById('ORACCColumns');

    const analyzeButtonSigns = document.getElementById('analyze-button-signs');
    const analyzeButtonWords = document.getElementById('analyze-button-words');
    const analyzeButtonGlossary = document.getElementById('analyze-button-glossary');
    const analyzeButtonORACC = document.getElementById('analyze-button-oracc');
    
    const downloadButtonCSV = document.getElementById('download-button-csv');
    const downloadButtonXLSX = document.getElementById('download-button-xlsx');
    const downloadButtonATF = document.getElementById('download-button-atf');
    
    const SERVER_URL = 'http://127.0.0.1:5000';

    let currentUploadId = null;
    let layout = 'lines'
    let currentAnalysis = null
    let obverseReverseState = "False"
    let columnsState = "False"

    analyzeButtonSigns.disabled = true;
    analyzeButtonWords.disabled = true;
    analyzeButtonGlossary.disabled = true;
    analyzeButtonORACC.disabled = true;
    downloadButtonCSV.disabled = true
    downloadButtonXLSX.disabled = true
    downloadButtonATF.disabled = true

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

    downloadButtonATF.addEventListener('click', (event) => {
        event.preventDefault();
        downloadFile('atf');
    });

    downloadButtonCSV.addEventListener('click', (event) => {
        event.preventDefault();
        downloadFile('csv');
    });

    downloadButtonXLSX.addEventListener('click', (event) => {
        event.preventDefault();
        downloadFile('xlsx');
    });

    function getSelectedLayout() {
        const selectedOption = document.querySelector('.layout-option.selected');
        return selectedOption ? selectedOption.dataset.layout : 'lines';
    }

    if (!columnsCheckbox || !obverseReverseCheckbox) {
        console.error("One or more required elements are missing.");
        return;
    }
    
    function updateStates() {
        columnsState = columnsCheckbox.checked ? "True" : "False";
        obverseReverseState = obverseReverseCheckbox.checked ? "True" : "False";
        
        console.log("States updated:", { columnsState, obverseReverseState });
    }

    columnsCheckbox.addEventListener('change', updateStates);
    obverseReverseCheckbox.addEventListener('change', updateStates);

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
                        errors.style.display = 'none'
                        output.textContent = `File uploaded: ${file.name}`;
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

    function renderTableSings(data) {
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

            const tableHTML = renderTableSings(jsonResult.analysis);
            document.getElementById('basic-output').innerHTML = tableHTML;

            errors.style.display = 'block'
            errors.textContent = `${JSON.stringify(jsonResult.syntax_errors)}`;

            downloadButtonATF.disabled = true
            downloadButtonCSV.disabled = false
            downloadButtonXLSX.disabled = false

            currentAnalysis = 'signs'

        } catch (error) {
            console.error('Error:', error);
            output.textContent = `Error: ${error.message}`;
        }
    }

    function renderTableWords(data) {
        let tableHTML = '<table><tr><th>attested form</th><th>preserved</th><th>partially preserved</th><th>reconstructed</th></tr>';
        
        for (let WordForm in data) {
            tableHTML += `<tr>
                <td>${WordForm}</td>
                <td>${data[WordForm]['preserved']}</td>
                <td>${data[WordForm]['partially preserved']}</td>
                <td>${data[WordForm]['reconstructed']}</td>
            </tr>`;
        }
        
        tableHTML += '</table>';
        return tableHTML;
    }

    async function analyzeWords() {
        console.log('Analyzing words');
        try {
            const response = await fetch(`${SERVER_URL}/analyzeWordsAction/${currentUploadId}`, {
                method: 'POST',
                });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const glossary_results = await response.text();
            console.log('Full response received. Size:', glossary_results.length);
            console.log('Parsing JSON...');
            const jsonResult = JSON.parse(glossary_results);
            console.log('JSON parsed successfully.');

            const tableHTML = renderTableWords(jsonResult.analysis);
            document.getElementById('basic-output').innerHTML = tableHTML;

            errors.style.display = 'none'

            downloadButtonATF.disabled = true
            downloadButtonCSV.disabled = false
            downloadButtonXLSX.disabled = false

            currentAnalysis = 'words'

        } catch (error) {
            console.error('Error:', error);
            output.textContent = `Error: ${error.message}`;
        }
    }

    function renderTableGlossary(data) {
        let tableHTML = '<table><tr><th>Attested form</th><th>attestation</th></tr>';
        
        for (let AttestedForm in data) {
            tableHTML += `<tr>
                <td>${AttestedForm}</td>
                <td>${data[AttestedForm]['attestation']}</td>
            </tr>`;
        }
        
        tableHTML += '</table>';
        return tableHTML;
    }

    async function analyzeGlossary() {
        console.log('Analyzing glossary');
        try {
            const response = await fetch(`${SERVER_URL}/analyzeGlossaryAction/${currentUploadId}`, {
                method: 'POST',
                });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const glossary_results = await response.text();
            console.log('Full response received. Size:', glossary_results.length);
            console.log('Parsing JSON...');
            const jsonResult = JSON.parse(glossary_results);
            console.log('JSON parsed successfully.');

            const tableHTML = renderTableGlossary(jsonResult.analysis);
            document.getElementById('basic-output').innerHTML = tableHTML;

            errors.style.display = 'none'

            downloadButtonATF.disabled = true
            downloadButtonCSV.disabled = false
            downloadButtonXLSX.disabled = false

            currentAnalysis = 'glossary'

        } catch (error) {
            console.error('Error:', error);
            output.textContent = `Error: ${error.message}`;
        }
    }
    
    async function analyzeORACC() {
        // if (columnsCheckbox.checked == true){
        //     columnsState = "True"
        // } else {
        //     columnsState = "False"
        // }

        // if (obverseReverseCheckbox.checked == true){
        //     obverseReverseState = "True"
        // } else {
        //     obverseReverseState = "False"
        // }

        console.log(obverseReverseState)
        console.log(columnsState)

        try {
            const response = await fetch(`${SERVER_URL}/analyzeORACCAction/${currentUploadId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    obverseReverse: obverseReverseState,
                    columns: columnsState
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const oracc_results = await response.json()
            // const jsonResult = JSON.parse(oracc_results);
            console.log('JSON parsed successfully.');

            document.getElementById('basic-output').innerHTML = oracc_results.as_html_data

            errors.style.display = 'block'
            errors.textContent = oracc_results.syntax_errors

            downloadButtonATF.disabled = false
            downloadButtonCSV.disabled = true
            downloadButtonXLSX.disabled = true

            currentAnalysis = 'oracc'

        } catch (error) {
            console.error('Error:', error);
            output.textContent = `Error: ${error.message}`;
        }
    }

    function downloadFile(format) {
        let endpoint = `${SERVER_URL}/download_${format}/${currentAnalysis}_${currentUploadId}`;
        window.location.href = endpoint;
    }

});