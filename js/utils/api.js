/**
 * API Utility Module
 * Централизованные функции для работы с API
 */

const API = {
    baseURL: '/api',

    /**
     * Выполняет GET запрос
     * @param {string} endpoint - Endpoint API
     * @param {Object} params - Query параметры
     * @returns {Promise<any>}
     */
    async get(endpoint, params = {}) {
        const url = new URL(this.baseURL + endpoint, window.location.origin);
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
                url.searchParams.append(key, params[key]);
            }
        });

        const response = await fetch(url, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        return this._handleResponse(response);
    },

    /**
     * Выполняет POST запрос с JSON данными
     * @param {string} endpoint - Endpoint API
     * @param {Object} data - Данные для отправки
     * @returns {Promise<any>}
     */
    async post(endpoint, data) {
        const response = await fetch(this.baseURL + endpoint, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        return this._handleResponse(response);
    },

    /**
     * Выполняет POST запрос с FormData
     * @param {string} endpoint - Endpoint API
     * @param {FormData} formData - FormData для отправки
     * @returns {Promise<any>}
     */
    async postFormData(endpoint, formData) {
        const response = await fetch(this.baseURL + endpoint, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });

        return this._handleResponse(response);
    },

    /**
     * Выполняет PUT запрос
     * @param {string} endpoint - Endpoint API
     * @param {Object} data - Данные для обновления
     * @returns {Promise<any>}
     */
    async put(endpoint, data) {
        const response = await fetch(this.baseURL + endpoint, {
            method: 'PUT',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        return this._handleResponse(response);
    },

    /**
     * Выполняет PUT запрос с FormData
     * @param {string} endpoint - Endpoint API
     * @param {FormData} formData - FormData для отправки
     * @returns {Promise<any>}
     */
    async putFormData(endpoint, formData) {
        const response = await fetch(this.baseURL + endpoint, {
            method: 'PUT',
            credentials: 'include',
            body: formData
        });

        return this._handleResponse(response);
    },

    /**
     * Выполняет DELETE запрос
     * @param {string} endpoint - Endpoint API
     * @returns {Promise<any>}
     */
    async delete(endpoint) {
        const response = await fetch(this.baseURL + endpoint, {
            method: 'DELETE',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        return this._handleResponse(response);
    },

    /**
     * Обрабатывает ответ от сервера
     * @param {Response} response - Fetch Response
     * @returns {Promise<any>}
     * @private
     */
    async _handleResponse(response) {
        // Если ответ не успешный, пытаемся получить сообщение об ошибке
        if (!response.ok) {
            let errorMessage = `HTTP Error ${response.status}`;

            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorData.message || errorMessage;
            } catch (e) {
                // Если не удалось распарсить JSON, используем текст
                try {
                    errorMessage = await response.text() || errorMessage;
                } catch (e2) {
                    // Используем дефолтное сообщение
                }
            }

            // Если 401, возможно истек токен
            if (response.status === 401) {
                // Пытаемся обновить токен
                try {
                    await this.refreshToken();
                    // Не кидаем ошибку, пусть вызывающий код попробует еще раз
                    return null;
                } catch (refreshError) {
                    // Если обновление не удалось, перенаправляем на логин
                    window.location.href = '/html/authorization.html';
                    throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
                }
            }

            throw new Error(errorMessage);
        }

        // Пытаемся распарсить JSON
        try {
            return await response.json();
        } catch (e) {
            // Если не JSON, возвращаем текст
            return await response.text();
        }
    },

    /**
     * Обновляет access token
     * @returns {Promise<any>}
     */
    async refreshToken() {
        const response = await fetch(this.baseURL + '/refreshToken', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Не удалось обновить токен');
        }

        return await response.json();
    },

    /**
     * Проверяет авторизацию пользователя
     * @returns {Promise<boolean>}
     */
    async checkAuth() {
        try {
            await this.get('/user/me');
            return true;
        } catch (error) {
            return false;
        }
    }
};

// Экспорт для использования в модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
}
