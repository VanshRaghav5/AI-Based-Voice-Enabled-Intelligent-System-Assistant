class StateManager {
    constructor() {
        this.state = {
            status: 'IDLE', // IDLE, STARTING, ACTIVE, STOPPING, ERROR
            isListening: true,
            networkMode: 'LOCAL',
            logs: [],
            error: null,
            version: '1.0.0'
        };
        this.listeners = [];
    }

    /**
     * Subscribe to state changes
     */
    subscribe(callback) {
        this.listeners.push(callback);
        // Immediately trigger with current state
        callback(this.state);
        return () => {
            this.listeners = this.listeners.filter(l => l !== callback);
        };
    }

    /**
     * Update partial state and notify listeners
     */
    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.notify();
    }

    /**
     * Notify all listeners of state change
     */
    notify() {
        this.listeners.forEach(callback => callback(this.state));
    }

    /**
     * Add a log entry
     */
    addLog(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const newLog = { timestamp, message, type };
        this.state.logs = [...this.state.logs, newLog].slice(-100); // Keep last 100 logs
        this.notify();
    }

    /**
     * Set the system status
     */
    setStatus(status) {
        this.setState({ status });
        this.addLog(`System status changed to ${status}`, 'system');
    }

    /**
     * Set network mode
     */
    setNetworkMode(mode) {
        this.setState({ networkMode: mode });
        this.addLog(`Network mode set to ${mode}`, 'network');
    }

    /**
     * Handle errors
     */
    setError(error) {
        this.setState({ error, status: 'ERROR' });
        if (error) {
            this.addLog(`ERROR: ${error}`, 'error');
        }
    }
}

// Create a singleton instance
const stateManager = new StateManager();
module.exports = stateManager;
