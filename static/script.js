const resumeInput = document.getElementById('resumes');
const fileSummary = document.getElementById('file-summary');
const formElement = document.getElementById('analyzeForm');
const loadingDiv = document.getElementById('loading');
const resultsSection = document.getElementById('results');
const submitBtn = document.getElementById('submitBtn');
const rankingList = document.getElementById('ranking-list');
const resultCount = document.getElementById('result-count');
const analyticsSection = document.getElementById('analytics');
const precisionTableBody = document.getElementById('precisionTableBody');
const insightStats = document.getElementById('insightStats');
const skillGapList = document.getElementById('skillGapList');

let scoreComparisonChartInstance = null;
let constraintPieChartInstance = null;

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
        renderAnalytics(data);
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
        const isEligible = item.g_hard !== 0;
        const statusClass = isEligible ? 'status-pass' : 'status-fail';
        const statusLabel = isEligible ? 'Eligible' : 'Failed hard constraints';
        const failedConstraints = Array.isArray(item.failed_constraints)
            ? item.failed_constraints
            : [];
        const failedConstraintHtml = failedConstraints.length > 0
            ? `<p class="constraint-fail">${failedConstraints.join(' | ')}</p>`
            : '';
        const highestEducation = item.highest_education || 'Unknown';
        const relevantYearsExperience = typeof item.relevant_years_experience === 'number'
            ? item.relevant_years_experience.toFixed(2)
            : '0.00';
        const totalYearsExperience = typeof item.total_years_experience === 'number'
            ? item.total_years_experience.toFixed(2)
            : '0.00';
        const cgpaValue = typeof item.cgpa_value === 'number'
            ? item.cgpa_value.toFixed(2)
            : 'N/A';

        card.innerHTML = `
            <header class="rank-header">
                <div>
                    <p class="rank-number">Rank #${item.rank}</p>
                    <h3 class="candidate-id">${item.resume_id}</h3>
                </div>
                <div class="score-pill">${scorePercent}%</div>
            </header>
            <p class="status-chip ${statusClass}">${statusLabel}</p>
            ${failedConstraintHtml}
            <div class="metric-row">
                <span>Embedding: ${formatMetric(item.embedding_similarity)}</span>
                <span>TF-IDF: ${formatMetric(item.tfidf_similarity)}</span>
                <span>Skill Overlap: ${formatMetric(item.skill_overlap_score)}</span>
                <span>Relevant Experience: ${relevantYearsExperience} years</span>
                <span>Total Experience: ${totalYearsExperience} years</span>
                <span>Education: ${highestEducation}</span>
                <span>CGPA: ${cgpaValue}</span>
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

function renderAnalytics(results) {
    if (!analyticsSection) {
        return;
    }

    analyticsSection.classList.remove('hidden');
    renderScoreComparisonChart(results);
    renderConstraintPieChart(results);
    renderPrecisionTable(results);
    renderHiringInsights(results);
}

function renderScoreComparisonChart(results) {
    const canvas = document.getElementById('scoreComparisonChart');
    if (!canvas || typeof Chart === 'undefined') {
        return;
    }

    const labels = results.map((item, index) => `Candidate ${index + 1}`);
    const embedding = results.map((item) => toPercent(item.embedding_similarity));
    const tfidf = results.map((item) => toPercent(item.tfidf_similarity));
    const skill = results.map((item) => toPercent(item.skill_overlap_score));
    const finalScore = results.map((item) => toPercent(item.score));

    if (scoreComparisonChartInstance) {
        scoreComparisonChartInstance.destroy();
    }

    scoreComparisonChartInstance = new Chart(canvas, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Embedding',
                    data: embedding,
                    backgroundColor: '#3b82f6',
                    borderRadius: 6,
                },
                {
                    label: 'TF-IDF',
                    data: tfidf,
                    backgroundColor: '#14b8a6',
                    borderRadius: 6,
                },
                {
                    label: 'Skill',
                    data: skill,
                    backgroundColor: '#f59e0b',
                    borderRadius: 6,
                },
                {
                    label: 'Final',
                    data: finalScore,
                    backgroundColor: '#8b5cf6',
                    borderRadius: 6,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Candidates',
                    },
                    ticks: {
                        maxRotation: 0,
                        minRotation: 0,
                    },
                    grid: {
                        display: false,
                    },
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Score',
                    },
                },
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        title: (items) => {
                            const i = items[0].dataIndex;
                            return results[i]?.resume_id || labels[i];
                        },
                        label: (context) => `${context.dataset.label}: ${context.raw.toFixed(1)}%`,
                    },
                },
            },
        },
    });
}

function renderConstraintPieChart(results) {
    const canvas = document.getElementById('constraintPieChart');
    if (!canvas || typeof Chart === 'undefined') {
        return;
    }

    const passed = results.filter((item) => item.g_hard !== 0).length;
    const failed = Math.max(0, results.length - passed);

    if (constraintPieChartInstance) {
        constraintPieChartInstance.destroy();
    }

    constraintPieChartInstance = new Chart(canvas, {
        type: 'pie',
        data: {
            labels: ['Passed', 'Failed'],
            datasets: [
                {
                    data: [passed, failed],
                    backgroundColor: ['#22c55e', '#ef4444'],
                    borderColor: '#ffffff',
                    borderWidth: 2,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const total = passed + failed || 1;
                            const value = context.raw;
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${context.label}: ${value} (${percentage}%)`;
                        },
                    },
                },
                legend: {
                    position: 'bottom',
                },
            },
        },
    });
}

function renderPrecisionTable(results) {
    if (!precisionTableBody) {
        return;
    }

    precisionTableBody.innerHTML = results
        .map((item) => {
            const state = item.g_hard !== 0 ? 'Passed' : 'Failed';
            return `
                <tr>
                    <td>${item.rank}</td>
                    <td class="candidate-col">${escapeHtml(item.resume_id || 'Unknown')}</td>
                    <td>${formatMetric(item.embedding_similarity)}</td>
                    <td>${formatMetric(item.tfidf_similarity)}</td>
                    <td>${formatMetric(item.skill_overlap_score)}</td>
                    <td><strong>${formatMetric(item.score)}</strong></td>
                    <td>${state}</td>
                </tr>
            `;
        })
        .join('');
}

function renderHiringInsights(results) {
    if (!insightStats || !skillGapList) {
        return;
    }

    const passedCandidates = results.filter((item) => item.g_hard !== 0);
    const passRate = results.length === 0 ? 0 : (passedCandidates.length / results.length) * 100;
    const avgFinal = average(results.map((item) => numeric(item.score)));
    const avgRelevantExperience = average(results.map((item) => numeric(item.relevant_years_experience)));
    const avgCgpa = average(
        results
            .map((item) => item.cgpa_value)
            .filter((value) => typeof value === 'number')
    );

    insightStats.innerHTML = `
        <div class="insight-pill">
            <span class="insight-label">Pass Rate</span>
            <span class="insight-value">${passRate.toFixed(1)}%</span>
        </div>
        <div class="insight-pill">
            <span class="insight-label">Avg Final Score</span>
            <span class="insight-value">${toPercent(avgFinal).toFixed(1)}%</span>
        </div>
        <div class="insight-pill">
            <span class="insight-label">Avg Relevant Experience</span>
            <span class="insight-value">${avgRelevantExperience.toFixed(2)} yrs</span>
        </div>
        <div class="insight-pill">
            <span class="insight-label">Avg CGPA</span>
            <span class="insight-value">${Number.isNaN(avgCgpa) ? 'N/A' : `${avgCgpa.toFixed(2)}/10`}</span>
        </div>
    `;

    const missingSkillCounts = {};
    results.forEach((item) => {
        const missing = Array.isArray(item.missing_skills) ? item.missing_skills : [];
        missing.forEach((skill) => {
            missingSkillCounts[skill] = (missingSkillCounts[skill] || 0) + 1;
        });
    });

    const topSkillGaps = Object.entries(missingSkillCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);

    if (topSkillGaps.length === 0) {
        skillGapList.innerHTML = '<p class="gap-empty">No significant skill gaps detected in this batch.</p>';
        return;
    }

    skillGapList.innerHTML = `
        <p class="gap-title">Top Missing Skills</p>
        <div class="gap-tags">
            ${topSkillGaps
                .map(([skill, count]) => `<span class="gap-tag">${escapeHtml(skill)} (${count})</span>`)
                .join('')}
        </div>
    `;
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

function numeric(value) {
    return typeof value === 'number' ? value : 0;
}

function average(values) {
    if (!values || values.length === 0) {
        return Number.NaN;
    }

    const sum = values.reduce((acc, value) => acc + numeric(value), 0);
    return sum / values.length;
}

function toPercent(value) {
    const safe = numeric(value);
    const bounded = Math.max(0, Math.min(1, safe));
    return bounded * 100;
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}