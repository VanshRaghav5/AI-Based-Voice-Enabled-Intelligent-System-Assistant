const stateManager = require('../services/stateManager');

class LogPanel {
    constructor(mountPointId) {
        this.container = document.getElementById(mountPointId);
        this.render();

        stateManager.subscribe((state) => this.update(state));
    }

    update(state) {
        const { logs } = state;
        const viewport = this.container;

        if (viewport) {
            // Only re-render if log count changed
            const currentCount = viewport.querySelectorAll('.log-entry').length;
            if (currentCount !== logs.length) {
                viewport.innerHTML = logs.map(log => `
                    <div class="log-entry ${log.type}">
                        <span class="log-time">[${log.timestamp}]</span>
                        <span class="log-msg">${log.message}</span>
                    </div>
                `).join('');

                // Auto-scroll to bottom
                viewport.scrollTop = viewport.scrollHeight;
            }
        }
    }

    render() {
        // Initial empty state
        this.container.innerHTML = `
            <div class="empty-logs">No execution logs yet...</div>
        `;
    }
}

module.exports = LogPanel;
