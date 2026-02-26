// authorizationFunctions.js
const API_CONFIG = window.API_CONFIG;
let tokenExpiry = null;
let refreshTimer = null;

function getRedirectAfterLogin() {
    const url = sessionStorage.getItem('redirectAfterLogin') || '/';
    sessionStorage.removeItem('redirectAfterLogin');
    const authPath = '/html/authorization.html';
    if (url === authPath || url.endsWith(authPath) || url.replace(/\/$/, '').endsWith(authPath.replace('.html', ''))) {
        return '/';
    }
    return url;
}

// Инициализация при загрузке модуля
if (typeof window !== 'undefined') {
    // Восстанавливаем время истечения токена из localStorage, если есть
    const savedExpiry = localStorage.getItem('tokenExpiry');
    if (savedExpiry && localStorage.getItem('isLoggedIn') === 'true') {
        tokenExpiry = parseInt(savedExpiry);
        // Проверяем, не истек ли уже токен
        if (tokenExpiry > Date.now()) {
            startTokenRefreshTimer();
        } else {
            // Токен истек, пытаемся обновить
            localStorage.removeItem('tokenExpiry');
            refreshToken().catch(() => {
                // Очищаем локальное состояние без редиректа (редирект сделает checkAuth при необходимости)
                if (localStorage.getItem('isLoggedIn')) {
                    if (refreshTimer) { clearTimeout(refreshTimer); refreshTimer = null; }
                    tokenExpiry = null;
                    localStorage.removeItem('isLoggedIn');
                    localStorage.removeItem('accessToken');
                    localStorage.removeItem('token');
                    localStorage.removeItem('userId');
                    localStorage.removeItem('username');
                    localStorage.removeItem('isAdmin');
                    sessionStorage.removeItem('trustLocalAuthUntil');
                    sessionStorage.removeItem('justLoggedIn');
                }
            });
        }
    }
}

export function register() {
    const email = document.getElementById('email').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
        alert('Пароли не совпадают!');
        return;
    }

    // Используем /api/register из registration_bp
    fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.REGISTER), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include',  // ВАЖНО: для работы с cookies
        body: JSON.stringify({
            email: email,
            username: username,
            password: password
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || 'Ошибка регистрации');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Регистрация успешна:', data.message);
        alert(data.message);
        sessionStorage.setItem('justLoggedIn', '1');
        sessionStorage.setItem('trustLocalAuthUntil', String(Date.now() + 60000));
        const target = getRedirectAfterLogin();
        setTimeout(() => { window.location.href = target; }, 150);
    })
    .catch(error => {
        console.error('Ошибка регистрации:', error);
        alert(error.message);
    });
}

export function authorize() {
    const login = document.getElementById('login').value;
    const password = document.getElementById('password').value;

    fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.LOGIN), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
            login: login,
            password: password
        })
    })
    .then(response => {
        // Сначала получаем текст, чтобы увидеть что пришло
        return response.text().then(text => {
            console.log('Raw response:', text);
            
            // Пытаемся парсить как JSON
            try {
                if (!response.ok) {
                    const err = JSON.parse(text);
                    throw new Error(err.error || 'Ошибка авторизации');
                }
                return JSON.parse(text);
            } catch (e) {
                // Если не JSON, проверяем HTML
                if (text.includes('<!DOCTYPE html>') || text.includes('<html')) {
                    console.error('Server returned HTML instead of JSON');
                    console.error('Response status:', response.status);
                    console.error('Response headers:', response.headers);
                    
                    if (response.status === 404) {
                        throw new Error('API endpoint not found (404). Check server routes.');
                    } else if (response.status === 500) {
                        throw new Error('Internal server error (500). Check server logs.');
                    } else {
                        throw new Error(`Server error: ${response.status}. Received HTML instead of JSON.`);
                    }
                }
                throw new Error(`Invalid response: ${text.substring(0, 100)}`);
            }
        });
    })
    .then(data => {
        console.log('Login successful:', data);
        localStorage.setItem('isLoggedIn', 'true');
        
        // Сохраняем информацию о пользователе
        if (data.userID) {
            localStorage.setItem('userId', data.userID.toString());
        }
        if (data.username) {
            localStorage.setItem('username', data.username);
        }
        
        // Устанавливаем время истечения токена для автоматического обновления
        if (data.accessExpiry) {
            tokenExpiry = new Date(data.accessExpiry).getTime();
            localStorage.setItem('tokenExpiry', tokenExpiry.toString());
            startTokenRefreshTimer();
        }
        sessionStorage.setItem('justLoggedIn', '1');
        sessionStorage.setItem('trustLocalAuthUntil', String(Date.now() + 60000));
        const target = getRedirectAfterLogin();
        setTimeout(() => { window.location.href = target; }, 150);
    })
    .catch(error => {
        console.error('Ошибка авторизации:', error);
        alert('Ошибка авторизации: ' + error.message);
    });
}

function startTokenRefreshTimer() {
    // Очищаем предыдущий таймер, если есть
    if (refreshTimer) {
        clearTimeout(refreshTimer);
        refreshTimer = null;
    }
    
    // Проверка: не запускаем таймер, если сессия сброшена
    if (!tokenExpiry || localStorage.getItem('isLoggedIn') !== 'true') {
        return;
    }

    const now = Date.now();
    const timeToExpiry = tokenExpiry - now;
    
    // Обновляем за 2 минуты до истечения (вместо 1 минуты для надежности)
    const refreshIn = Math.max(60000, timeToExpiry - (2 * 60 * 1000)); // минимум 1 минута, или 2 мин до expiry
    
    console.log(`Таймер обновления токена установлен на ${Math.round(refreshIn / 1000)} секунд`);

    refreshTimer = setTimeout(() => {
        // Повторная проверка перед обновлением
        if (localStorage.getItem('isLoggedIn') !== 'true') {
            console.log('Сессия сброшена — обновление токена отменено');
            clearTimeout(refreshTimer);
            refreshTimer = null;
            tokenExpiry = null;
            return;
        }

        console.log('Автоматическое обновление токена...');
        refreshToken().then(() => {
            refreshTimer = null;
            console.log('Токен успешно обновлен автоматически');
        }).catch(error => {
            console.error('Ошибка автоматического обновления токена:', error);
            refreshTimer = null;
            // Не вызываем logout сразу, может быть временная ошибка
            // Только если точно unauthorized
            if (error.message && error.message.includes('unauthorized')) {
                logout();
            }
        });
    }, refreshIn);
}

export function refreshToken() {
    return fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.REFRESH_TOKEN), {
        method: 'POST',
        credentials: 'include' // Включаем cookies в запрос
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                logout();
                throw new Error('Refresh failed: unauthorized');
            }
            throw new Error('Refresh failed');
        }
        return response.json();
    })
    .then(data => {
        console.log('Токен обновлён:', data.message);
        if (data.accessExpiry) {
            tokenExpiry = new Date(data.accessExpiry).getTime();
            localStorage.setItem('tokenExpiry', tokenExpiry.toString());
            startTokenRefreshTimer();
        }
        return data;
    })
    .catch(error => {
        console.error('Ошибка обновления токена:', error);
        // Не вызываем logout сразу, может быть временная ошибка сети
        if (error.message.includes('unauthorized')) {
            logout();
        }
        throw error;
    });
}

export function logout() {
    // Остановка таймера обновления токена
    if (refreshTimer) {
        clearTimeout(refreshTimer);
        refreshTimer = null;
    }
    tokenExpiry = null;
    
    // Очистка localStorage
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    localStorage.removeItem('username');
    localStorage.removeItem('isAdmin');
    localStorage.removeItem('tokenExpiry');
    
    // Очистка sessionStorage
    sessionStorage.clear();
    
    // Отправляем запрос на сервер (не ждем ответа)
    fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.LOGOUT), {
        method: 'POST',
        credentials: 'include'
    }).catch(error => {
        console.error('Ошибка логаута на сервере:', error);
    });
    
    // Редирект
    window.location.href = '/html/authorization.html';
}

// Глобальный перехватчик fetch для автоматического обновления токена
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

// Перехватчик для автоматического обновления токена (только для API запросов)
const originalFetch = window.fetch;
window.fetch = function(...args) {
    // Нормализуем аргументы
    let url, options = {};
    if (typeof args[0] === 'string') {
        url = args[0];
        options = args[1] || {};
    } else {
        url = args[0].url;
        options = { ...args[0] };
    }
    
    const isApiRequest = url && url.includes('/api/');
    
    // Убеждаемся, что credentials включены для API запросов
    if (isApiRequest && !options.credentials) {
        options.credentials = 'include';
    }
    
    // Создаем новый массив аргументов
    const newArgs = typeof args[0] === 'string' 
        ? [url, options]
        : [{ ...args[0], ...options }];
    
    return originalFetch.apply(this, newArgs)
        .then(response => {
            // Если получили 401 на API запросе, пытаемся обновить токен
            if (response.status === 401 && isApiRequest && 
                !url.includes('/refreshToken') && 
                !url.includes('/login') && 
                !url.includes('/register')) {
                
                if (!isRefreshing) {
                    isRefreshing = true;
                    return refreshToken()
                        .then(() => {
                            isRefreshing = false;
                            processQueue(null, true);
                            // Повторяем оригинальный запрос с обновленными cookies
                            return originalFetch.apply(this, newArgs);
                        })
                        .catch(err => {
                            isRefreshing = false;
                            processQueue(err, null);
                            // Если refresh не удался и это критичный запрос
                            if (localStorage.getItem('isLoggedIn') && 
                                (url.includes('/validate-token') || url.includes('/users/'))) {
                                // Для критичных запросов - редирект на логин
                                setTimeout(() => logout(), 100);
                            }
                            return response;
                        });
                } else {
                    // Токен уже обновляется, ждем
                    return new Promise((resolve, reject) => {
                        failedQueue.push({ resolve, reject });
                    }).then(() => {
                        return originalFetch.apply(this, newArgs);
                    }).catch(() => response);
                }
            }
            return response;
        });
};

// Функция проверки авторизации (переиспользуемая)
export function checkAuth(redirectIfUnauthorized = true) {
    if (localStorage.getItem('isLoggedIn') !== 'true') {
        if (redirectIfUnauthorized) {
            sessionStorage.setItem('redirectAfterLogin', window.location.href);
            window.location.href = '/html/authorization.html';
        }
        throw new Error('Не авторизован');
    }
    const justLoggedIn = sessionStorage.getItem('justLoggedIn');
    if (justLoggedIn) {
        setTimeout(() => sessionStorage.removeItem('justLoggedIn'), 2500);
        const uid = localStorage.getItem('userId');
        if (uid) return Promise.resolve(parseInt(uid, 10));
    }
    const trustUntil = sessionStorage.getItem('trustLocalAuthUntil');
    if (trustUntil && Date.now() < parseInt(trustUntil, 10)) {
        const uid = localStorage.getItem('userId');
        if (uid) return Promise.resolve(parseInt(uid, 10));
    }
    function doValidate() {
        return fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.VALIDATE_TOKEN), {
            method: 'GET',
            credentials: 'include'
        })
            .then(response => response.ok ? response.json() : response.json().then(() => { throw new Error('Ошибка сервера'); }))
            .then(data => {
                if (data.valid === false || !data.userID) {
                    return Promise.reject(data);
                }
                if (data.userID) localStorage.setItem('userId', data.userID.toString());
                if (data.username) localStorage.setItem('username', data.username);
                if (data.isAdmin !== undefined) localStorage.setItem('isAdmin', data.isAdmin.toString());
                if (data.accessExpiry) {
                    const tokenExpiry = new Date(data.accessExpiry).getTime();
                    localStorage.setItem('tokenExpiry', tokenExpiry.toString());
                    startTokenRefreshTimer();
                }
                return data.userID;
            });
    }
    return doValidate()
        .catch(dataOrErr => {
            const isValidateResponse = dataOrErr && typeof dataOrErr === 'object' && dataOrErr.valid === false;
            if (isValidateResponse) {
                return refreshToken().then(() => doValidate());
            }
            throw dataOrErr;
        })
        .catch(error => {
            const isUnauth = (error && typeof error === 'object' && error.valid === false) || (error && error.message === 'Не авторизован');
            if (isUnauth) {
                sessionStorage.removeItem('trustLocalAuthUntil');
                localStorage.removeItem('isLoggedIn');
                if (redirectIfUnauthorized) {
                    sessionStorage.setItem('redirectAfterLogin', window.location.href);
                    window.location.href = '/html/authorization.html';
                }
            }
            console.error('Ошибка проверки авторизации:', error);
            throw error instanceof Error ? error : new Error('Не авторизован');
        });
}

// Функция для получения заголовков с токеном (если есть)
export function getAuthHeaders(additionalHeaders = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...additionalHeaders
    };
    
    // Пытаемся получить токен из localStorage
    const token = localStorage.getItem('accessToken');
    
    // Добавляем Authorization только если токен есть и он валидный
    if (token && token !== 'null' && token !== 'undefined' && token.trim() !== '') {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
}

// Функция проверки, является ли пользователь администратором
export async function checkIsAdmin() {
    try {
        // Проверяем кэш
        const cachedIsAdmin = localStorage.getItem('isAdmin');
        if (cachedIsAdmin === 'true') {
            return true;
        }
        
        // Используем cookies для валидации
        const response = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.VALIDATE_TOKEN), {
            method: 'GET',
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                // Пытаемся обновить токен
                try {
                    await refreshToken();
                    const retryResponse = await fetch(API_CONFIG.buildURL(API_CONFIG.ENDPOINTS.VALIDATE_TOKEN), {
                        method: 'GET',
                        credentials: 'include'
                    });
                    if (!retryResponse.ok) return false;
                    const data = await retryResponse.json();
                    localStorage.setItem('isAdmin', data.isAdmin ? 'true' : 'false');
                    return data.isAdmin === true;
                } catch (e) {
                    return false;
                }
            }
            return false;
        }
        
        const data = await response.json();
        localStorage.setItem('isAdmin', data.isAdmin ? 'true' : 'false');
        return data.isAdmin === true;
    } catch (error) {
        console.error('Ошибка проверки прав администратора:', error);
        return false;
    }
}


