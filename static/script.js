// 1. Handle File Selection Display
document.getElementById('resume').addEventListener('change', function(e) {
    const fileName = e.target.files[0] ? e.target.files[0].name : "No file selected";
    document.getElementById('file-name').textContent = fileName;
});

// 2. Handle Form Submission
document.getElementById('analyzeForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const submitBtn = document.getElementById('submitBtn');

    // UI State: Loading
    loadingDiv.classList.remove('hidden');
    resultsDiv.classList.add('hidden');
    submitBtn.disabled = true;
    submitBtn.textContent = "Analyzing...";

    fetch('/analyze', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // UI State: Done
        loadingDiv.classList.add('hidden');
        submitBtn.disabled = false;
        submitBtn.textContent = "Analyze Match";

        if (data.error) {
            alert(data.error);
            return;
        }

        // Update Score & Category
        document.getElementById('match_score').textContent = data.match_score + '%';
        document.getElementById('resume_category').textContent = data.resume_category;

        // Render Skills as Tags
        renderTags(data.matched_skills, 'matched_skills', 'tag-match');
        renderTags(data.missing_skills, 'missing_skills', 'tag-missing');

        resultsDiv.classList.remove('hidden');
    })
    .catch(error => {
        console.error('Error:', error);
        loadingDiv.classList.add('hidden');
        submitBtn.disabled = false;
        alert("An error occurred. Check console.");
    });
});

// Helper function to create badges
function renderTags(skills, containerId, className) {
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Clear previous

    if (skills.length === 0) {
        container.innerHTML = '<span class="text-light">None detected</span>';
        return;
    }

    skills.forEach(skill => {
        const span = document.createElement('span');
        span.className = `tag ${className}`;
        span.textContent = skill;
        container.appendChild(span);
    });
}