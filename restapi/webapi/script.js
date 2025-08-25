// Navigation functionality
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');
const navLinks = document.querySelectorAll('.nav-link');

hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    navMenu.classList.toggle('active');
});

navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetPage = link.getAttribute('data-page');
        showPage(targetPage);
                
        // Update active nav link
        navLinks.forEach(nl => nl.classList.remove('active'));
        link.classList.add('active');
                
        // Close mobile menu
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
    });
});

// Page navigation
    function showPage(pageName) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));
        document.getElementById(pageName).classList.add('active');
}

// RNA sequence validation
function validateRNASequence(sequence) {
    const rnaPattern = /^[AUGC\s]*$/i;
    const cleanSequence = sequence.replace(/\s/g, '').toUpperCase();
    return {
        isValid: rnaPattern.test(cleanSequence),
        cleanSequence: cleanSequence
    };
}

// Dot-bracket structure validation
function validateDotBracket(structure) {
    const dotBracketPattern = /^[\.\(\)]*$/;
    const cleanStructure = structure.replace(/\s/g, '');
            
    if (!dotBracketPattern.test(cleanStructure)) {
        return { isValid: false, message: 'Only dots (.), opening (, and closing ) parentheses are allowed' };
    }

    // Check balanced parentheses
    let count = 0;
    for (let char of cleanStructure) {
        if (char === '(') count++;
        else if (char === ')') count--;
        if (count < 0) {
            return { isValid: false, message: 'Unbalanced parentheses: closing bracket without matching opening bracket' };        }
            }

        if (count !== 0) {
                return { isValid: false, message: 'Unbalanced parentheses: unmatched opening brackets' };}

            return { isValid: true, cleanStructure: cleanStructure };
        }

// Form handling
document.getElementById('rna-form').addEventListener('submit', async function(e) {
    e.preventDefault();
            
    const sequenceInput = document.getElementById('rna-sequence');
    const structureInput = document.getElementById('dot-bracket');
    const sequenceError = document.getElementById('sequence-error');
    const structureError = document.getElementById('structure-error');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const submitBtn = document.getElementById('submit-btn');

    // Clear previous errors
    sequenceError.textContent = '';
    structureError.textContent = '';
            
    const sequence = sequenceInput.value.trim();
    const structure = structureInput.value.trim();

    // Validation
    let hasErrors = false;

    if (!sequence) {
        sequenceError.textContent = 'RNA sequence is required';
        hasErrors = true;
    } else {
        const sequenceValidation = validateRNASequence(sequence);
        if (!sequenceValidation.isValid) {
            sequenceError.textContent = 'Invalid RNA sequence. Only A, U, G, C nucleotides are allowed';
            hasErrors = true;
        }
    }

    if (!structure) {
        structureError.textContent = 'Dot-bracket structure is required';
        hasErrors = true;
    } else {
        const structureValidation = validateDotBracket(structure);
        if (!structureValidation.isValid) {
            structureError.textContent = structureValidation.message;
            hasErrors = true;
        }
    }

    // Check if sequence and structure lengths match
    if (!hasErrors) {
        const cleanSequence = validateRNASequence(sequence).cleanSequence;
        const cleanStructure = validateDotBracket(structure).cleanStructure;
                
        if (cleanSequence.length !== cleanStructure.length) {
            structureError.textContent = `Structure length (${cleanStructure.length}) must match sequence length (${cleanSequence.length})`;
            hasErrors = true;
        }
    }

    if (hasErrors) return;

    // Show loading state
    loading.style.display = 'block';
    results.style.display = 'none';
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';

    try {
        // Placeholder for API call - replace with actual endpoint
        const result = await classifyRNA(sequence, structure);
        displayResults(result);
    } catch (error) {
        console.error('Classification error:', error);
        alert('An error occurred during classification. Please try again.');
    } finally {
        loading.style.display = 'none';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Classify RNA';
    }
    });

// Placeholder function for API call - TO BE IMPLEMENTED
async function classifyRNA(sequence, structure) {
// Simulate API call with mock data for demonstration
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                classification: {
                    family: "tRNA",
                    subfamily: "tRNA-Phe",
                    confidence: 0.89,
                    features: ["Cloverleaf structure", "A loop", "B loop"]
                },
                similarities: [
                    {
                        id: "RF00005",
                        name: "tRNA",
                        similarity: 0.94,
                        description: "Transfer RNA family"
                    },
                    {
                        id: "RF00001",
                        name: "5S_rRNA",
                        similarity: 0.32,
                        description: "5S ribosomal RNA"
                    }
                ]
            });
        }, 2000);

    });

            // Actual implementation would be:
            /*
            const response = await fetch('/api/classify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sequence: validateRNASequence(sequence).cleanSequence,
                    structure: validateDotBracket(structure).cleanStructure
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
            */
}

// Display results function
function displayResults(data) {
    const classificationOutput = document.getElementById('classification-output');
    const similarityMatches = document.getElementById('similarity-matches');
    const results = document.getElementById('results');

    // Display classification results
    classificationOutput.innerHTML = `
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h4 style="color: #333; margin-bottom: 1rem;">Primary Classification</h4>
            <p><strong>Family:</strong> ${data.classification.family}</p>
            <p><strong>Subfamily:</strong> ${data.classification.subfamily}</p>
            <p><strong>Confidence:</strong> ${(data.classification.confidence * 100).toFixed(1)}%</p>
            <div style="margin-top: 1rem;">
                <strong>Structural Features:</strong>
                <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                    ${data.classification.features.map(feature => `<li>${feature}</li>`).join('')}</ul>
            </div>
        </div>
        `
        ;

    // Display similarity matches
    similarityMatches.innerHTML = data.similarities.map(match => 
    `
        <div class="similarity-match">
            <h4 style="color: #333; margin-bottom: 0.5rem;">${match.name} (${match.id})</h4>
            <p style="color: #666; margin-bottom: 0.5rem;">${match.description}</p>
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span><strong>Similarity:</strong> ${(match.similarity * 100).toFixed(1)}%</span>
                <div style="flex: 1; background: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="width: ${match.similarity * 100}%; height: 100%; background: linear-gradient(90deg, #667eea, #764ba2);"></div>
                </div>
            </div>
        </div>
    `
    ).join('');

    results.style.display = 'block';
}

// Export functionality (placeholder)
document.getElementById('export-btn').addEventListener('click', function() {
    // Placeholder for export functionality
    alert('Export functionality will be implemented with backend integration. Results would be exported as JSON/CSV format.');
            
            // Future implementation:
            /*
            const resultsData = {
                timestamp: new Date().toISOString(),
                sequence: document.getElementById('rna-sequence').value,
                structure: document.getElementById('dot-bracket').value,
                results: currentResults // Would store the current results
            };
            
            const blob = new Blob([JSON.stringify(resultsData, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `rna-classification-${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
            */
});

// Real-time validation feedback
document.getElementById('rna-sequence').addEventListener('input', function(e) {
    const sequence = e.target.value.trim();
    const error = document.getElementById('sequence-error');
            
    if (sequence && !validateRNASequence(sequence).isValid) {
        error.textContent = 'Invalid characters detected. Only A, U, G, C nucleotides are allowed';
    } else {
        error.textContent = '';
    }
});

document.getElementById('dot-bracket').addEventListener('input', function(e) {
    const structure = e.target.value.trim();
    const error = document.getElementById('structure-error');
            
    if (structure) {
        const validation = validateDotBracket(structure);
        if (!validation.isValid) {
            error.textContent = validation.message;
        } else {
            error.textContent = '';
        }
    } else{error.textContent = '';}
});