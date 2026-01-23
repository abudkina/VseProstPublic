// API Configuration
const API_CONFIG = {
    BASE_URL: window.location.origin,
    API_PATH: '/api',
    get API_URL() {
        return this.BASE_URL + this.API_PATH;
    }
};

// Helper function to get API URL (works in both module and non-module contexts)
export function getApiUrl() {
    return window.location.origin + '/api';
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API_CONFIG;
}
