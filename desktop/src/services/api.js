const axios = require('axios');

class ApiService {
    constructor(baseURL = 'http://localhost:8000') {
        this.client = axios.create({
            baseURL,
            timeout: 5000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    /**
     * Check if the backend is reachable
     */
    async checkHealth() {
        try {
            await this.client.get('/status', { timeout: 2000 });
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * Get the current status of the voice assistant
     */
    async getStatus() {
        try {
            const response = await this.client.get('/status');
            return response.data;
        } catch (error) {
            console.error('API Error (getStatus):', error.message);
            throw error;
        }
    }

    /**
     * Start the voice assistant
     */
    async startAssistant() {
        try {
            const response = await this.client.post('/start');
            return response.data;
        } catch (error) {
            console.error('API Error (startAssistant):', error.message);
            throw error;
        }
    }

    /**
     * Stop the voice assistant
     */
    async stopAssistant() {
        try {
            const response = await this.client.post('/stop');
            return response.data;
        } catch (error) {
            console.error('API Error (stopAssistant):', error.message);
            throw error;
        }
    }

    /**
     * Get system logs
     */
    async getLogs() {
        try {
            const response = await this.client.get('/logs');
            return response.data;
        } catch (error) {
            console.error('API Error (getLogs):', error.message);
            throw error;
        }
    }

    /**
     * Toggle always-listening mode
     */
    async toggleListening(enabled) {
        try {
            const response = await this.client.post('/config/listening', { enabled });
            return response.data;
        } catch (error) {
            console.error('API Error (toggleListening):', error.message);
            throw error;
        }
    }
}

module.exports = new ApiService();
