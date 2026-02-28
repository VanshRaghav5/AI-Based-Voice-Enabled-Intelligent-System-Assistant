const stateManager = require('../services/stateManager');

class NotificationToast {
    constructor(mountPointId) {
        this.container = document.getElementById(mountPointId);

        // Listen for errors specifically
        stateManager.subscribe((state) => {
            if (state.error && state.error !== this.lastError) {
                this.show(state.error, 'error');
                this.lastError = state.error;
            }
        });
    }

    show(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">!</span>
                <span class="toast-msg">${message}</span>
            </div>
            <button class="toast-close">&times;</button>
        `;

        this.container.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => this.remove(toast), 5000);

        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.remove(toast);
        });
    }

    remove(toast) {
        toast.classList.add('fading');
        setTimeout(() => toast.remove(), 300);
    }
}

module.exports = NotificationToast;
