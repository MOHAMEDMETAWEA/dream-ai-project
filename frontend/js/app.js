/**
 * DreamAI frontend logic.
 */

'use strict';

const API_BASE = window.location.protocol === 'file:'
    ? 'http://localhost:5000/api'
    : `${window.location.origin}/api`;

let currentUser = null;
let emotionChart = null;
let timelineChart = null;
let recognition = null;
let isRecording = false;
let currentDreamId = null;

const EMOTION_CLASSES = {
    fear: 'emotion-fear',
    stress: 'emotion-stress',
    sadness: 'emotion-sadness',
    happiness: 'emotion-happiness',
    neutral: 'emotion-neutral',
    unknown: 'emotion-unknown',
    pending: 'emotion-unknown',
};

const EMOTION_INSIGHTS = {
    fear: 'Your dream contains themes associated with fear or anxiety. Reflect on what might be causing apprehension in your waking life.',
    stress: 'The content of your dream suggests stress-related themes. Consider whether there are pressures in your daily routine that may be appearing during sleep.',
    sadness: 'Your dream shows emotional themes linked to sadness or loss. It may help to acknowledge and process any difficult feelings you are carrying.',
    happiness: 'Your dream reflects positive and joyful emotional content. This often aligns with comfort, connection, or something you are looking forward to.',
    neutral: 'Your dream appears to have a neutral emotional tone. Dreams with mixed or unclear content are completely normal.',
    unknown: 'We could not clearly identify the emotional theme of this dream. Try adding more detail to your description for a more accurate analysis.',
};

const PAGES = ['auth', 'dashboard', 'record', 'history'];

document.addEventListener('DOMContentLoaded', () => {
    initVoiceInput();
    checkSession();
});

async function checkSession() {
    try {
        const res = await fetch(`${API_BASE}/me`, { credentials: 'include' });
        if (!res.ok) {
            showPage('auth');
            return;
        }

        const data = await res.json();
        currentUser = data.username;
        showApp();
    } catch (error) {
        showPage('auth');
    }
}

function switchTab(tab) {
    document.getElementById('form-login').classList.toggle('hidden', tab !== 'login');
    document.getElementById('form-register').classList.toggle('hidden', tab !== 'register');
    document.getElementById('tab-login').classList.toggle('active', tab === 'login');
    document.getElementById('tab-register').classList.toggle('active', tab === 'register');
    document.getElementById('auth-error').classList.add('hidden');
}

async function doLogin() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    if (!username || !password) {
        showAuthError('Please fill in both fields.');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password }),
        });
        const data = await res.json();

        if (!res.ok) {
            showAuthError(data.error || 'Login failed.');
            return;
        }

        currentUser = data.username;
        showApp();
    } catch (error) {
        showAuthError('Could not connect to the server. Is the backend running?');
    }
}

async function doRegister() {
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;

    if (!username || !password) {
        showAuthError('Please fill in username and password.');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, email, password }),
        });
        const data = await res.json();

        if (!res.ok) {
            showAuthError(data.error || 'Registration failed.');
            return;
        }

        currentUser = data.username;
        showApp();
    } catch (error) {
        showAuthError('Could not connect to the server.');
    }
}

async function logout() {
    try {
        await fetch(`${API_BASE}/logout`, { method: 'POST', credentials: 'include' });
    } catch (error) {
        // Ignore logout errors and return to auth screen anyway.
    }

    currentUser = null;
    destroyCharts();
    document.getElementById('navbar').classList.add('hidden');
    showPage('auth');
}

function showAuthError(message) {
    const element = document.getElementById('auth-error');
    element.textContent = message;
    element.classList.remove('hidden');
}

function showPage(name) {
    PAGES.forEach((page) => {
        document.getElementById(`page-${page}`).classList.add('hidden');
    });
    document.getElementById(`page-${name}`).classList.remove('hidden');

    document.querySelectorAll('.nav-btn').forEach((button) => button.classList.remove('active'));
    const activeButton = document.querySelector(`.nav-btn[onclick*="${name}"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }

    if (name === 'dashboard') {
        loadDashboard();
    }
    if (name === 'history') {
        loadDreamHistory();
    }
}

function showApp() {
    document.getElementById('navbar').classList.remove('hidden');
    document.getElementById('nav-username').textContent = `User: ${currentUser}`;
    showPage('dashboard');
}

async function loadDashboard() {
    try {
        const res = await fetch(`${API_BASE}/dashboard`, { credentials: 'include' });
        if (!res.ok) {
            return;
        }

        const data = await res.json();
        const distribution = data.emotion_distribution || {};
        const topEmotion = Object.keys(distribution).length > 0
            ? Object.entries(distribution).sort((left, right) => right[1] - left[1])[0][0]
            : '-';

        document.getElementById('stat-total').textContent = data.total_dreams ?? 0;
        document.getElementById('stat-top-emotion').textContent = topEmotion;
        document.getElementById('stat-patterns').textContent = (data.recurring_patterns || []).length;

        renderEmotionChart(distribution);
        renderTimelineChart(data.timeline || []);
        renderPatterns(data.recurring_patterns || []);
    } catch (error) {
        console.error('Dashboard load error:', error);
    }
}

function renderEmotionChart(distribution) {
    const labels = Object.keys(distribution);
    const values = Object.values(distribution);
    const colours = {
        fear: '#e85b5b',
        stress: '#ffa000',
        sadness: '#5b7fe8',
        happiness: '#4caf7d',
        neutral: '#8896b3',
        unknown: '#8896b3',
    };

    const ctx = document.getElementById('emotionChart').getContext('2d');
    if (emotionChart) {
        emotionChart.destroy();
    }

    if (labels.length === 0) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        ctx.fillStyle = '#8896b3';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('No data yet - record your first dream.', ctx.canvas.width / 2, 110);
        return;
    }

    emotionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map((label) => label.charAt(0).toUpperCase() + label.slice(1)),
            datasets: [{
                data: values,
                backgroundColor: labels.map((label) => colours[label] || '#8896b3'),
                borderColor: '#1A2540',
                borderWidth: 3,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#8896b3', font: { size: 12 } },
                },
            },
        },
    });
}

function renderTimelineChart(timeline) {
    const ctx = document.getElementById('timelineChart').getContext('2d');
    if (timelineChart) {
        timelineChart.destroy();
    }

    timelineChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: timeline.map((entry) => entry.date),
            datasets: [{
                label: 'Dreams recorded',
                data: timeline.map((entry) => entry.count),
                backgroundColor: 'rgba(91,127,232,0.6)',
                borderColor: '#5b7fe8',
                borderWidth: 2,
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#8896b3', font: { size: 10 } }, grid: { color: '#2C3B60' } },
                y: { ticks: { color: '#8896b3', stepSize: 1 }, grid: { color: '#2C3B60' }, beginAtZero: true },
            },
        },
    });
}

function renderPatterns(patterns) {
    const container = document.getElementById('patterns-list');
    if (!patterns.length) {
        container.innerHTML = '<p class="empty-msg">Record at least 2 dreams to see recurring patterns.</p>';
        return;
    }

    container.innerHTML = patterns.map((pattern) =>
        `<div class="pattern-tag">${escapeHtml(pattern.word)}<span>x${pattern.count}</span></div>`
    ).join('');
}

function destroyCharts() {
    if (emotionChart) {
        emotionChart.destroy();
        emotionChart = null;
    }
    if (timelineChart) {
        timelineChart.destroy();
        timelineChart = null;
    }
}

function updateCharCount() {
    const text = document.getElementById('dream-text').value;
    document.getElementById('char-count').textContent = `${text.length} / 5000`;
}

async function submitDream() {
    const text = document.getElementById('dream-text').value.trim();
    const title = document.getElementById('dream-title').value.trim();

    if (text.length < 10) {
        showRecordError('Please describe your dream in more detail (at least 10 characters).');
        return;
    }

    document.getElementById('record-error').classList.add('hidden');
    document.getElementById('result-panel').classList.add('hidden');
    document.getElementById('btn-analyse').disabled = true;
    showLoading('Analysing your dream...');

    try {
        const res = await fetch(`${API_BASE}/dreams`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ text, title }),
        });
        const data = await res.json();

        if (!res.ok) {
            showRecordError(data.error || 'Analysis failed. Please try again.');
            return;
        }

        showAnalysisResult(data.emotion, data.confidence);
    } catch (error) {
        showRecordError('Could not connect to the server.');
    } finally {
        hideLoading();
        document.getElementById('btn-analyse').disabled = false;
    }
}

function showAnalysisResult(emotion, confidence) {
    const panel = document.getElementById('result-panel');
    const badge = document.getElementById('result-emotion-badge');

    badge.textContent = emotion;
    badge.className = `emotion-badge ${EMOTION_CLASSES[emotion] || 'emotion-unknown'}`;
    document.getElementById('result-confidence').textContent = `${confidence}%`;
    document.getElementById('result-insight').textContent = EMOTION_INSIGHTS[emotion] || EMOTION_INSIGHTS.unknown;

    panel.classList.remove('hidden');
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showRecordError(message) {
    const element = document.getElementById('record-error');
    element.textContent = message;
    element.classList.remove('hidden');
}

function clearDreamForm() {
    document.getElementById('dream-text').value = '';
    document.getElementById('dream-title').value = '';
    document.getElementById('char-count').textContent = '0 / 5000';
    document.getElementById('record-error').classList.add('hidden');
    document.getElementById('result-panel').classList.add('hidden');
}

function initVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        document.getElementById('voice-unsupported').classList.remove('hidden');
        return;
    }

    document.getElementById('voice-section').classList.remove('hidden');

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    let finalTranscript = '';

    recognition.onresult = (event) => {
        let interimTranscript = '';
        for (let index = event.resultIndex; index < event.results.length; index += 1) {
            if (event.results[index].isFinal) {
                finalTranscript += `${event.results[index][0].transcript} `;
            } else {
                interimTranscript += event.results[index][0].transcript;
            }
        }

        const currentText = document.getElementById('dream-text').value;
        const base = currentText.replace(/\[Listening: .*?\]$/, '').trimEnd();
        document.getElementById('dream-text').value =
            base + (base ? ' ' : '') + finalTranscript + (interimTranscript ? `[Listening: ${interimTranscript}]` : '');
        updateCharCount();
    };

    recognition.onerror = (event) => {
        document.getElementById('voice-status').textContent = `Voice error: ${event.error}`;
        stopVoice();
    };

    recognition.onend = () => {
        if (isRecording) {
            stopVoice();
        }
    };
}

function toggleVoice() {
    if (isRecording) {
        stopVoice();
        return;
    }
    startVoice();
}

function startVoice() {
    if (!recognition) {
        return;
    }

    isRecording = true;
    document.getElementById('btn-voice').textContent = 'Stop Recording';
    document.getElementById('btn-voice').classList.add('recording');
    document.getElementById('voice-status').textContent = 'Listening...';
    recognition.start();
}

function stopVoice() {
    isRecording = false;
    if (recognition) {
        try {
            recognition.stop();
        } catch (error) {
            // Ignore duplicate stop requests.
        }
    }

    document.getElementById('btn-voice').textContent = 'Start Voice Input';
    document.getElementById('btn-voice').classList.remove('recording');
    document.getElementById('voice-status').textContent = 'Recording stopped.';

    const textarea = document.getElementById('dream-text');
    textarea.value = textarea.value.replace(/\[Listening: .*?\]/, '').trimEnd();
    updateCharCount();
}

async function loadDreamHistory() {
    const container = document.getElementById('dreams-list');
    container.innerHTML = '<p class="empty-msg">Loading...</p>';

    try {
        const res = await fetch(`${API_BASE}/dreams`, { credentials: 'include' });
        if (!res.ok) {
            container.innerHTML = '<p class="empty-msg">Failed to load dreams.</p>';
            return;
        }

        const dreams = await res.json();
        if (!dreams.length) {
            container.innerHTML = '<p class="empty-msg">No dreams yet. Go to Record Dream to start.</p>';
            return;
        }

        container.innerHTML = dreams.map((dream) => `
            <div class="dream-item" onclick="openDreamModal(${dream.id})">
                <div class="dream-item-left">
                    <div class="dream-item-title">${escapeHtml(dream.title)}</div>
                    <div class="dream-item-preview">${escapeHtml(dream.content)}</div>
                    <div class="dream-item-meta">${formatDate(dream.created_at)}</div>
                </div>
                <div class="dream-item-right">
                    <span class="emotion-badge sm ${EMOTION_CLASSES[dream.emotion] || 'emotion-unknown'}">
                        ${escapeHtml(dream.emotion)}
                    </span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = '<p class="empty-msg">Failed to load dreams.</p>';
    }
}

async function openDreamModal(dreamId) {
    currentDreamId = dreamId;

    try {
        const res = await fetch(`${API_BASE}/dreams/${dreamId}`, { credentials: 'include' });
        if (!res.ok) {
            return;
        }

        const dream = await res.json();
        document.getElementById('modal-title').textContent = dream.title;
        document.getElementById('modal-date').textContent = formatDate(dream.created_at);
        document.getElementById('modal-content').textContent = dream.content;
        document.getElementById('modal-confidence').textContent = `Confidence: ${dream.confidence}%`;

        const badge = document.getElementById('modal-emotion-badge');
        badge.textContent = dream.emotion;
        badge.className = `emotion-badge sm ${EMOTION_CLASSES[dream.emotion] || 'emotion-unknown'}`;

        const keywordsContainer = document.getElementById('modal-keywords-list');
        if (!Array.isArray(dream.keywords) || dream.keywords.length === 0) {
            keywordsContainer.innerHTML = '<p class="empty-msg">No keywords available.</p>';
        } else {
            keywordsContainer.innerHTML = dream.keywords.map((keyword) =>
                `<div class="pattern-tag">${escapeHtml(keyword)}</div>`
            ).join('');
        }

        document.getElementById('modal-overlay').classList.remove('hidden');
    } catch (error) {
        console.error('Modal load error:', error);
    }
}

function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
    currentDreamId = null;
}

async function deleteDream() {
    if (!currentDreamId) {
        return;
    }
    if (!confirm('Are you sure you want to delete this dream? This cannot be undone.')) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/dreams/${currentDreamId}`, {
            method: 'DELETE',
            credentials: 'include',
        });
        if (res.ok) {
            closeModal();
            loadDreamHistory();
        }
    } catch (error) {
        alert('Failed to delete dream.');
    }
}

function showLoading(message = 'Please wait...') {
    document.getElementById('loading-text').textContent = message;
    document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

async function exportData() {
    try {
        const res = await fetch(`${API_BASE}/export`, { credentials: 'include' });
        if (!res.ok) {
            alert('Export failed. Please try again.');
            return;
        }

        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `dreamai-export-${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    } catch (error) {
        alert('Could not export data.');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(String(text)));
    return div.innerHTML;
}

function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}
