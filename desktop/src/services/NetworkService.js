const api = require('./api');
const stateManager = require('./stateManager');

class NetworkService {
    constructor() {
        this.pollingInterval = null;
        this.isOnline = false;
    }

    /**
     * Start continuous monitoring of backend health
     */
    startMonitoring() {
        if (this.pollingInterval) return;

        console.log('Network Monitoring Started');

        // Initial check
        this.performCheck();

        // Set up interval (every 5 seconds)
        this.pollingInterval = setInterval(() => {
            this.performCheck();
        }, 5000);
    }

    /**
     * Stop monitoring
     */
    stopMonitoring() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    /**
     * Perform a single health check
     */
    async performCheck() {
        const reachable = await api.checkHealth();

        if (reachable !== this.isOnline) {
            this.isOnline = reachable;
            const mode = reachable ? 'LOCAL (CONNECTED)' : 'OFFLINE';

            stateManager.setNetworkMode(mode);

            if (reachable) {
                stateManager.addLog('Backend connection established.', 'system');
                this.syncSystemStatus();
            } else {
                stateManager.addLog('Backend disconnected. Retrying...', 'error');
            }
        }
    }

    /**
     * Fetch full system status from backend
     */
    async syncSystemStatus() {
        try {
            const data = await api.getStatus();
            if (data) {
                if (data.status) stateManager.setStatus(data.status);
                if (typeof data.listening === 'boolean') stateManager.setState({ isListening: data.listening });
            }
        } catch (error) {
            console.warn('Sync failed:', error.message);
        }
    }
}

module.exports = new NetworkService();
