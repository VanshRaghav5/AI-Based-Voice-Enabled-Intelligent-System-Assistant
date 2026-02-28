const stateManager = require('../services/stateManager');
const api = require('../services/api');

class ControlPanel {
    constructor(mountPointId) {
        this.container = document.getElementById(mountPointId);
        this.render();
        this.attachEvents();

        stateManager.subscribe((state) => this.update(state));
    }

    async handleAction(action) {
        try {
            if (action === 'START') {
                stateManager.setStatus('STARTING');
                await api.startAssistant();
                stateManager.setStatus('ACTIVE');
            } else if (action === 'STOP') {
                stateManager.setStatus('STOPPING');
                await api.stopAssistant();
                stateManager.setStatus('IDLE');
            }
        } catch (error) {
            stateManager.setError(error.message);
        }
    }

    async toggleListening() {
        const newState = !stateManager.state.isListening;
        try {
            await api.toggleListening(newState);
            stateManager.setState({ isListening: newState });
            stateManager.addLog(`Always-listening ${newState ? 'enabled' : 'disabled'}`, 'config');
        } catch (error) {
            stateManager.setError('Failed to toggle listening mode');
        }
    }

    update(state) {
        const { status, isListening } = state;
        const startBtn = this.container.querySelector('.btn-start');
        const stopBtn = this.container.querySelector('.btn-stop');
        const toggle = this.container.querySelector('.toggle-input');

        if (startBtn && stopBtn) {
            startBtn.disabled = (status === 'ACTIVE' || status === 'STARTING');
            stopBtn.disabled = (status === 'IDLE' || status === 'STOPPING');
        }

        if (toggle) {
            toggle.checked = isListening;
        }
    }

    attachEvents() {
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('.btn-start')) this.handleAction('START');
            if (e.target.closest('.btn-stop')) this.handleAction('STOP');
            if (e.target.closest('.toggle-slider')) this.toggleListening();
        });
    }

    render() {
        this.container.innerHTML = `
            <div class="control-grid">
                <button class="action-btn btn-start">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                    <span>Start Assistant</span>
                </button>
                <button class="action-btn btn-stop" disabled>
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="6" width="12" height="12"></rect></svg>
                    <span>Stop System</span>
                </button>
                
                <div class="setting-card">
                    <div class="setting-info">
                        <span class="setting-title">Always Listening</span>
                        <span class="setting-desc">Voice activation via wake-word</span>
                    </div>
                    <label class="toggle-switch">
                        <input type="checkbox" class="toggle-input" checked>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
            </div>
            <style>
                .control-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr) 1.5fr;
                    gap: 16px;
                    margin-bottom: 32px;
                }
                .action-btn {
                    background: var(--bg-surface);
                    border: 1px solid var(--border);
                    color: #fff;
                    padding: 20px;
                    border-radius: 16px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                    font-weight: 600;
                }
                .action-btn:hover:not(:disabled) {
                    background: rgba(255,255,255,0.05);
                    border-color: var(--primary);
                    transform: translateY(-2px);
                }
                .action-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                .btn-start { color: var(--success); }
                .btn-stop { color: var(--danger); }
                
                .setting-card {
                    background: var(--bg-surface);
                    border: 1px solid var(--border);
                    padding: 16px 24px;
                    border-radius: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }
                .setting-title { display: block; font-size: 13px; font-weight: 700; color: #fff; }
                .setting-desc { font-size: 11px; color: var(--text-dim); }
                
                .toggle-switch { position: relative; width: 44px; height: 24px; }
                .toggle-input { opacity: 0; width: 0; height: 0; }
                .toggle-slider {
                    position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
                    background-color: #334155; transition: .4s; border-radius: 34px;
                }
                .toggle-slider:before {
                    position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px;
                    background-color: white; transition: .4s; border-radius: 50%;
                }
                .toggle-input:checked + .toggle-slider { background-color: var(--primary); }
                .toggle-input:checked + .toggle-slider:before { transform: translateX(20px); }
            </style>
        `;
    }
}

module.exports = ControlPanel;
