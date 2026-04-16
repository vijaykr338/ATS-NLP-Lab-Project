const resumeInput = document.getElementById('resumes');
const fileSummary = document.getElementById('file-summary');
const formElement = document.getElementById('analyzeForm');
const loadingDiv = document.getElementById('loading');
const resultsSection = document.getElementById('results');
const submitBtn = document.getElementById('submitBtn');
const rankingList = document.getElementById('ranking-list');
const resultCount = document.getElementById('result-count');

resumeInput.addEventListener('change', function (event) {
    const files = event.target.files;
    if (!files || files.length === 0) {
        fileSummary.textContent = 'No files selected';
        return;
    }

    if (files.length === 1) {
        fileSummary.textContent = `1 file selected: ${files[0].name}`;
        return;
    }

    fileSummary.textContent = `${files.length} files selected`;
});

formElement.addEventListener('submit', async function (event) {
    event.preventDefault();

    const formData = new FormData(formElement);
    loadingDiv.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Ranking...';

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Analysis failed');
        }

        if (!Array.isArray(data) || data.length === 0) {
            throw new Error('No valid resumes were processed');
        }

        renderRankedResults(data);
        resultsSection.classList.remove('hidden');
    } catch (error) {
        console.error(error);
        alert(error.message || 'An unexpected error occurred');
    } finally {
        loadingDiv.classList.add('hidden');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Rank Candidates';
    }
});

function renderRankedResults(results) {
    rankingList.innerHTML = '';
    resultCount.textContent = `${results.length} result${results.length > 1 ? 's' : ''}`;

    results.forEach((item) => {
        const card = document.createElement('article');
        card.className = 'rank-card';

        const scorePercent = (item.score * 100).toFixed(1);

        card.innerHTML = `
            <header class="rank-header">
                <div>
                    <p class="rank-number">Rank #${item.rank}</p>
                    <h3 class="candidate-id">${item.resume_id}</h3>
                </div>
                <div class="score-pill">${scorePercent}%</div>
            </header>
            <div class="metric-row">
                <span>Embedding: ${formatMetric(item.embedding_similarity)}</span>
                <span>TF-IDF: ${formatMetric(item.tfidf_similarity)}</span>
                <span>Skill Overlap: ${formatMetric(item.skill_overlap_score)}</span>
            </div>
            <p class="explanation">${item.explanation}</p>
            <div class="tag-group">
                <h4>Matched Skills</h4>
                <div class="tags">${renderTags(item.matched_skills, 'match')}</div>
            </div>
            <div class="tag-group">
                <h4>Missing Skills</h4>
                <div class="tags">${renderTags(item.missing_skills, 'missing')}</div>
            </div>
        `;

        rankingList.appendChild(card);
    });
}

function renderTags(skills, type) {
    if (!skills || skills.length === 0) {
        return '<span class="tag neutral">None</span>';
    }

    return skills
        .map((skill) => `<span class="tag ${type}">${skill}</span>`)
        .join('');
}

function formatMetric(value) {
    if (typeof value !== 'number') {
        return '0.00';
    }
    return value.toFixed(2);
}