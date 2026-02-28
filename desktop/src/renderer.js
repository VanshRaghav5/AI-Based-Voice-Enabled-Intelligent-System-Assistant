/**
 * Main Renderer Process
 * Connects UI components with services and manages application lifecycle.
 */

const stateManager = require('./services/stateManager');
const StatusIndicator = require('./components/StatusIndicator');
const ControlPanel = require('./components/ControlPanel');
const LogPanel = require('./components/LogPanel');
const NotificationToast = require('./components/NotificationToast');
const networkService = require('./services/NetworkService');

// Initialize Components once DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Renderer process initialized');

    // Mount Components
    new StatusIndicator('status-mount');
    new ControlPanel('control-mount');
    new LogPanel('log-mount');
    new NotificationToast('notification-mount');

    // Start background network monitoring
    networkService.startMonitoring();

    // Initial system greeting
    stateManager.addLog('Aether AI Desktop Experience Layer Started.', 'system');

    // Check for app version via bridged API
    try {
        const version = await window.electronAPI.getAppVersion();
        stateManager.setState({ version });
    } catch (e) {
        console.warn('Could not fetch app version from main process');
    }
});
