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
                this.syncLogs();
            } else {
                stateManager.addLog('Backend disconnected. Retrying...', 'error');
            }
        } else if (reachable) {
            // Periodic sync when already connected
            this.syncLogs();
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

    /**
     * Fetch execution logs from backend
     */
    async syncLogs() {
        try {
            const logData = await api.getLogs();
            if (logData && Array.isArray(logData.logs)) {
                stateManager.setLogs(logData.logs);
            }
        } catch (error) {
            console.warn('Log sync failed:', error.message);
        }
    }
}

module.exports = new NetworkService();
