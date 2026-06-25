/**
 * Конфигурация API для VseProst
 * Централизованное управление URL и настройками API
 */

const SITE = window.SITE_CONFIG || {};

const API_CONFIG = {
    // На GitHub Pages fetch перехватывается js/static-api.js (data/site.json)
    BASE_URL: SITE.apiOrigin || window.location.origin,

    // Путь к API
    API_PATH: '/api',

    // Полный URL API
    get API_URL() {
        return this.BASE_URL + this.API_PATH;
    },

    // Таймауты
    TIMEOUT: {
        DEFAULT: 30000,  // 30 секунд
        LONG: 60000,     // 60 секунд для длительных операций
        SHORT: 10000     // 10 секунд для быстрых операций
    },

    // Пагинация
    PAGINATION: {
        DEFAULT_LIMIT: 50,
        MAX_LIMIT: 100
    },

    // Endpoints (используйте API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.LOGIN))
    ENDPOINTS: {
        // Auth
        LOGIN: '/login',
        REGISTER: '/register',
        LOGOUT: '/logout',
        REFRESH_TOKEN: '/refreshToken',
        VALIDATE_TOKEN: '/validate-token',
        FORGOT_PASSWORD: '/forgot-password',
        RESET_PASSWORD: '/reset-password',

        // Problems
        PROBLEMS: '/problems',
        PROBLEMS_FAVORITES: '/problems/favorites',
        PROBLEM_BY_ID: (id) => `/problems/${id}`,
        PROBLEM_TOGGLE_FAVORITE: (id) => `/problems/${id}/toggle-favourite`,

        // Solutions
        SOLUTIONS: '/solutions',
        SOLUTIONS_FAVORITES: '/solutions/favorites',
        SOLUTION_BY_ID: (id) => `/solutions/${id}`,
        SOLUTION_TOGGLE_FAVORITE: (id) => `/solutions/${id}/toggle-favourite`,

        // Hashtags, Categories, Topics
        HASHTAGS: '/hashtags',
        CATEGORIES: '/categories',
        TOPICS: '/topics',

        // Cart
        CART: '/cart',
        CART_COUNT: '/cart/count',

        // Notifications
        NOTIFICATIONS: '/notifications',
        NOTIFICATIONS_COUNT: '/notifications/count'
    },

    // Построить полный URL
    buildURL(endpoint) {
        return this.API_URL + endpoint;
    },

    // Построить URL с параметрами
    buildURLWithParams(endpoint, params = {}) {
        const url = new URL(this.buildURL(endpoint));
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });
        return url.toString();
    }
};

// Глобальный доступ для всех скриптов
window.API_CONFIG = API_CONFIG;

// Helper function (для обратной совместимости)
function getApiUrl() {
    return API_CONFIG.API_URL;
}
window.getApiUrl = getApiUrl;

// Export for Node/module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API_CONFIG;
}

// Dev mode logging
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('🔧 API Config loaded:', API_CONFIG.API_URL);
}
