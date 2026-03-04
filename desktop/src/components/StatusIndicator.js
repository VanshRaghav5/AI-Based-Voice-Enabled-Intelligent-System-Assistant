const stateManager = require('../services/stateManager');

class StatusIndicator {
    constructor(mountPointId) {
        this.container = document.getElementById(mountPointId);
        this.render();

        // Subscribe to state changes
        stateManager.subscribe((state) => this.update(state));
    }

    update(state) {
        const { status, networkMode } = state;
        const statusEl = this.container.querySelector('.status-indicator');
        const textEl = this.container.querySelector('.status-label');

        // Update Network Badge in header (direct DOM access for performance)
        const badge = document.getElementById('network-badge');
        const badgeText = document.querySelector('.network-text');
        if (badge && badgeText) {
            const isOnline = networkMode !== 'OFFLINE';
            badge.className = `network-badge ${isOnline ? 'online' : 'offline'}`;
            badgeText.textContent = networkMode;
        }

        if (statusEl && textEl) {
            // If offline, override status visual to show disconnected
            const displayStatus = (networkMode === 'OFFLINE') ? 'ERROR' : status;

            // Reset classes
            statusEl.className = 'status-indicator';
            statusEl.classList.add(displayStatus.toLowerCase());
            textEl.textContent = (networkMode === 'OFFLINE') ? 'DISCONNECTED' : status.replace('_', ' ');
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="status-widget">
                <div class="status-indicator"></div>
                <div class="status-info">
                    <span class="status-label">LOADING...</span>
                    <span class="status-helper">System Pulse</span>
                </div>
            </div>
            <style>
                .status-widget {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    padding: 20px;
                    background: var(--bg-glass);
                    backdrop-filter: blur(var(--glass-blur));
                    border: 1px solid var(--border);
                    border-radius: 20px;
                    margin-bottom: 32px;
                }
                .status-indicator {
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    background: var(--text-dim);
                    position: relative;
                }
                .status-indicator::after {
                    content: '';
                    position: absolute;
                    top: -4px;
                    left: -4px;
                    right: -4px;
                    bottom: -4px;
                    border-radius: 50%;
                    border: 2px solid currentColor;
                    opacity: 0.2;
                    animation: pulse 2s infinite;
                }
                .status-indicator.active { background: var(--success); color: var(--success); }
                .status-indicator.idle { background: var(--primary); color: var(--primary); }
                .status-indicator.starting { background: var(--secondary); color: var(--secondary); }
                .status-indicator.error { background: var(--danger); color: var(--danger); }
                
                .status-info { display: flex; flex-direction: column; }
                .status-label { font-size: 14px; font-weight: 700; color: #fff; text-transform: uppercase; letter-spacing: 1px; }
                .status-helper { font-size: 11px; color: var(--text-dim); font-weight: 500; }
                
                @keyframes pulse {
                    0% { transform: scale(1); opacity: 0.5; }
                    100% { transform: scale(2); opacity: 0; }
                }
            </style>
        `;
    }
}

module.exports = StatusIndicator;
