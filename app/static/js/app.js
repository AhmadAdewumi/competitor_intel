// app/static/js/app.js
// ============================================
// COMPETITORINTEL - Frontend Application
// ============================================

(function() {
    'use strict';

    // ============================================
    // STATE
    // ============================================

    let topics = [];
    let currentRunId = null;
    let eventSource = null;

    // ============================================
    // DOM REFERENCES
    // ============================================

    const topicsContainer = document.getElementById('topics-container');
    const tracePanel = document.getElementById('trace-panel');
    const traceBody = document.getElementById('trace-body');
    const traceTitle = document.getElementById('trace-title');
    const btnNewTopic = document.getElementById('btn-new-topic');
    const btnRefresh = document.getElementById('btn-refresh');
    const btnCloseTrace = document.getElementById('btn-close-trace');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnCancelModal = document.getElementById('btn-cancel-modal');
    const btnSaveTopic = document.getElementById('btn-save-topic');
    const topicModal = document.getElementById('topic-modal');
    const modalTitle = document.getElementById('modal-title');
    const topicForm = document.getElementById('topic-form');

    // ============================================
    // API HELPERS
    // ============================================

    async function fetchTopics() {
        try {
            const response = await fetch('/api/topics');
            const data = await response.json();
            topics = data.topics || [];
            renderTopics();
        } catch (error) {
            console.error('Failed to fetch topics:', error);
            topicsContainer.innerHTML = '<div class="loading">Error loading topics</div>';
        }
    }

    async function runTopic(topicId) {
        try {
            const response = await fetch(`/api/topics/${topicId}/run`, {
                method: 'POST'
            });
            const data = await response.json();
            if (data.run_id) {
                currentRunId = data.run_id;
                openTrace(data.run_id);
                startSSE(data.run_id);
            }
        } catch (error) {
            console.error('Failed to run topic:', error);
        }
    }

    // ============================================
    // RENDER FUNCTIONS
    // ============================================

    function renderTopics() {
    if (!topics || topics.length === 0) {
        topicsContainer.innerHTML = `
            <div class="loading" style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-secondary);">
                <div style="font-size: 24px; margin-bottom: 8px;">📋</div>
                <div>No topics yet</div>
                <div style="font-size: 13px; margin-top: 4px;">Click "New Topic" to create your first research topic</div>
            </div>
        `;
        return;
    }

    let html = '';
    for (const topic of topics) {
        const status = getTopicStatus(topic);
        html += `
            <div class="topic-card" data-topic-id="${topic.id}">
                <div class="topic-header">
                    <span class="topic-name">${escapeHtml(topic.name)}</span>
                    <span class="topic-status badge ${status.class}">${status.label}</span>
                </div>
                <div class="topic-description">${escapeHtml(topic.description || 'No description')}</div>
                <div class="topic-meta">
                    <span>📋 ${topic.search_terms?.length || 0} search terms</span>
                    <span>🔗 ${topic.urls?.length || 0} URLs</span>
                    <span>📧 ${topic.email || 'No email'}</span>
                    <span>📅 ${topic.schedule_frequency || 'Manual'}</span>
                </div>
                <div class="topic-actions">
                    <button class="btn btn-sm btn-primary" onclick="window.runTopic(${topic.id})">Run</button>
                    <button class="btn btn-sm btn-outline" onclick="window.editTopic(${topic.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="window.deleteTopic(${topic.id})">Delete</button>
                </div>
            </div>
        `;
    }
    topicsContainer.innerHTML = html;
}

    function getTopicStatus(topic) {
        // Check if running
        if (topic.running) {
            return { label: 'Running...', class: 'badge-running' };
        }
        // Check latest report
        if (topic.latest_report) {
            if (topic.latest_report.status === 'failed') {
                return { label: 'Failed', class: 'badge-error' };
            }
            return { label: `✓ ${formatTime(topic.latest_report.created_at)}`, class: 'badge-success' };
        }
        return { label: 'Pending', class: '' };
    }

    function formatTime(timestamp) {
        if (!timestamp) return 'Never';
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;
            if (diff < 60000) return 'Just now';
            if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
            if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
            return date.toLocaleDateString();
        } catch {
            return timestamp;
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ============================================
    // TRACE / SSE
    // ============================================

    function openTrace(runId) {
        tracePanel.style.display = 'flex';
        traceTitle.textContent = `Running... (${runId})`;
        traceBody.innerHTML = '<div class="trace-placeholder">⏳ Waiting for trace data...</div>';
        document.getElementById('trace-title').textContent = 'Running...';
    }

    function startSSE(runId) {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }

        eventSource = new EventSource(`/api/stream/${runId}`);

        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleTraceEvent(data);
            } catch (e) {
                // Ignore
            }
        };

        eventSource.onerror = function() {
            // Reconnect after delay
            setTimeout(() => {
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                    // Try to reconnect
                }
            }, 3000);
        };

        // Also fetch existing traces
        fetch(`/api/traces/${runId}`)
            .then(response => response.json())
            .then(data => {
                if (data.traces && data.traces.length > 0) {
                    traceBody.innerHTML = '';
                    for (const trace of data.traces) {
                        addTraceEntry(trace);
                    }
                }
            })
            .catch(console.error);
    }

    function handleTraceEvent(event) {
        if (event.type === 'trace') {
            addTraceEntry(event.data);
        } else if (event.type === 'complete') {
            addTraceEntry({
                agent: 'System',
                action: event.data.status === 'success' ? '✅ Complete' : '❌ Failed',
                content: event.data.message || '',
                timestamp: new Date().toLocaleTimeString()
            });
            document.getElementById('trace-title').textContent = 'Complete';
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
            // Refresh topics after completion
            setTimeout(fetchTopics, 2000);
        } else if (event.type === 'error') {
            addTraceEntry({
                agent: 'Error',
                action: event.data.message || 'Unknown error',
                content: '',
                timestamp: new Date().toLocaleTimeString()
            });
            document.getElementById('trace-title').textContent = 'Error';
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
        } else if (event.type === 'start') {
            document.getElementById('trace-title').textContent = 'Starting...';
        }
    }

    function addTraceEntry(trace) {
        // Remove placeholder if present
        const placeholder = traceBody.querySelector('.trace-placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        const entry = document.createElement('div');
        entry.className = 'trace-entry';

        const time = document.createElement('span');
        time.className = 'time';
        time.textContent = trace.timestamp || new Date().toLocaleTimeString();

        const agent = document.createElement('span');
        agent.className = 'agent';
        agent.textContent = trace.agent || 'System';

        const action = document.createElement('span');
        action.className = 'action';
        action.textContent = trace.action || '';

        const content = document.createElement('span');
        content.className = 'content';
        content.textContent = trace.content || '';

        entry.appendChild(time);
        entry.appendChild(agent);
        entry.appendChild(action);
        if (trace.content) {
            entry.appendChild(content);
        }

        traceBody.appendChild(entry);
        traceBody.scrollTop = traceBody.scrollHeight;
    }

    // ============================================
    // MODAL HANDLING
    // ============================================

    let editingTopicId = null;

    function openModal(topicId) {
        editingTopicId = topicId;
        topicForm.reset();

        if (topicId) {
            // Edit mode
            modalTitle.textContent = 'Edit Topic';
            const topic = topics.find(t => t.id === topicId);
            if (topic) {
                document.getElementById('topic-name').value = topic.name || '';
                document.getElementById('topic-description').value = topic.description || '';
                document.getElementById('topic-search-terms').value = (topic.search_terms || []).join('\n');
                document.getElementById('topic-urls').value = (topic.urls || []).join('\n');
                document.getElementById('topic-email').value = topic.email || '';
                document.getElementById('topic-schedule-freq').value = topic.schedule_frequency || '';
                document.getElementById('topic-schedule-time').value = topic.schedule_time || '09:00';
                document.getElementById('topic-schedule-day').value = topic.schedule_day || 'monday';
            }
        } else {
            // New topic mode
            modalTitle.textContent = 'New Topic';
            document.getElementById('topic-name').value = '';
            document.getElementById('topic-description').value = '';
            document.getElementById('topic-search-terms').value = '';
            document.getElementById('topic-urls').value = '';
            document.getElementById('topic-email').value = '';
            document.getElementById('topic-schedule-freq').value = '';
            document.getElementById('topic-schedule-time').value = '09:00';
            document.getElementById('topic-schedule-day').value = 'monday';
        }

        topicModal.style.display = 'flex';
    }

    function closeModal() {
        topicModal.style.display = 'none';
        editingTopicId = null;
    }

    async function saveTopic() {
        const data = {
            name: document.getElementById('topic-name').value.trim(),
            description: document.getElementById('topic-description').value.trim(),
            search_terms: document.getElementById('topic-search-terms').value.split('\n').filter(s => s.trim()),
            urls: document.getElementById('topic-urls').value.split('\n').filter(s => s.trim()),
            email: document.getElementById('topic-email').value.trim(),
            schedule_frequency: document.getElementById('topic-schedule-freq').value,
            schedule_time: document.getElementById('topic-schedule-time').value,
            schedule_day: document.getElementById('topic-schedule-day').value
        };

        if (!data.name) {
            alert('Topic name is required');
            return;
        }

        try {
            let response;
            if (editingTopicId) {
                response = await fetch(`/api/topics/${editingTopicId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            } else {
                response = await fetch('/api/topics', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            }

            if (response.ok) {
                closeModal();
                fetchTopics();
            } else {
                const error = await response.json();
                alert('Failed to save: ' + (error.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Failed to save topic:', error);
            alert('Failed to save topic');
        }
    }

    // ============================================
    // GLOBAL FUNCTIONS (for inline onclick)
    // ============================================

    window.runTopic = runTopic;
    window.editTopic = function(topicId) {
        openModal(topicId);
    };
    window.deleteTopic = async function(topicId) {
        if (!confirm('Delete this topic and all associated reports?')) return;
        try {
            const response = await fetch(`/api/topics/${topicId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                fetchTopics();
            }
        } catch (error) {
            console.error('Failed to delete topic:', error);
        }
    };

    // ============================================
    // EVENT LISTENERS
    // ============================================

    btnNewTopic.addEventListener('click', () => openModal(null));
    btnRefresh.addEventListener('click', fetchTopics);
    btnCloseTrace.addEventListener('click', () => {
        tracePanel.style.display = 'none';
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    });
    btnCloseModal.addEventListener('click', closeModal);
    btnCancelModal.addEventListener('click', closeModal);
    btnSaveTopic.addEventListener('click', saveTopic);

    // Close modal on backdrop click
    topicModal.addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });

    // Enter key on form
    topicForm.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            saveTopic();
        }
    });

    // ============================================
    // INIT
    // ============================================

    fetchTopics();

    // Refresh topics every 30 seconds
    setInterval(fetchTopics, 30000);

})();