let tokenExpiry = null;
let refreshTimer = null;

   export function register() {
    const email = document.getElementById('email').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
        alert('Пароли не совпадают!');
        return;
    }

    // AJAX-запрос для регистрации
    fetch('http://127.0.0.1:8080/api/register', {
        method: 'POST',
        headers: {
           'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
            email: email,
            username: username,
            password: password
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.message || 'Ошибка регистрации');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log(data.message);
        alert(data.message);
        // После успешной регистрации — сохраните токены и запустите таймер (если сервер вернул их)
        if (data.accessToken && data.expiry) {
            accessToken = data.accessToken;
            tokenExpiry = data.expiry;
            startTokenRefreshTimer();
        }
        window.location.href = '../html/authorization.html';
    })
    .catch(error => {
        console.error('Ошибка регистрации:', error);
        alert(error.message);
    });
}

export function authorize() {
    
    const login = document.getElementById('login').value;
    const password = document.getElementById('password').value;

    // AJAX-запрос для авторизации
    fetch('http://127.0.0.1:8080/api/login', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include', // Для работы с куками
        body: JSON.stringify({
            login: login,
            password: password
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.message || 'Ошибка авторизации');
            });
        }
        return response.json();
    })
    .then(data => {
        // После успешной авторизации — сохраните expiry и запустите таймер
        if (data.token || data.accessToken) {
            localStorage.setItem('token', data.token || data.accessToken);
            console.log('Токен сохранен в localStorage');
        } else {
            console.log('Токен не пришел в ответе (возможно, в куках)');
        }
        if (data.accessExpiry) {
            tokenExpiry = new Date(data.accessExpiry).getTime();
            console.log('tokenExpiry установлен:', tokenExpiry);
            if (isNaN(tokenExpiry)) {
                console.error('Неверная дата accessExpiry:', data.accessExpiry);
            } else {
                startTokenRefreshTimer();
            }
        } else {
            console.warn('accessExpiry отсутствует в ответе!');
        }
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('isLoggedIn', 'true');
        const redirectUrl = sessionStorage.getItem('redirectAfterLogin') || '../html/index.html';
        sessionStorage.removeItem('redirectAfterLogin');
        window.location.href = redirectUrl; // Редирект после логина
    })
    .catch(error => {
        console.error('Ошибка авторизации:', error);
        alert(error.message);
    });
}

 function startTokenRefreshTimer() {
    // Проверка: не запускаем таймер, если сессия сброшена или уже запущена
    if (!tokenExpiry || refreshTimer || localStorage.getItem('isLoggedIn') !== 'true') return;

    const now = Date.now();
    const timeToExpiry = tokenExpiry - now;
    const refreshIn = Math.max(0, timeToExpiry - (1 * 60 * 1000)); // 1 мин до expiry

    refreshTimer = setTimeout(() => {
        // Повторная проверка перед обновлением: если сессия сброшена, остановить таймер
        if (localStorage.getItem('isLoggedIn') !== 'true') {
            console.log('Сессия сброшена — обновление токена отменено');
            clearTimeout(refreshTimer);
            refreshTimer = null;
            tokenExpiry = null;
            return;
        }

        refreshToken().then(() => {
            refreshTimer = null;
        }).catch(error => {
            console.error('Ошибка обновления токена:', error);
            // Опционально: вызвать logout() при ошибке обновления
            logout();
        });
    }, refreshIn);
}

function refreshToken() {
    makeAuthenticatedRequest('http://127.0.0.1:8080/api/refreshToken', {
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
            startTokenRefreshTimer();
        }
        return data;
    })
    .catch(error => {
        console.error('Ошибка обновления токена:', error);
        logout();
        throw error;
    });
}

export function logout() {
    fetch('http://127.0.0.1:8080/api/logout', {
        method: 'POST',
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) throw new Error('Logout failed');
        return response.json();
    })
    .then(data => {
        console.log(data.message);
        // Очистка localStorage (предотвращает "вечную" сессию)
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('token');
        // Очистка sessionStorage (существующая логика)
        sessionStorage.clear();
        // Остановка таймера обновления токена
        clearTimeout(refreshTimer);
        refreshTimer = null;
        tokenExpiry = null;
        // Редирект
        window.location.href = '../html/authorization.html';
    })
    .catch(error => {
        console.error('Ошибка логаута:', error);
        // В случае ошибки тоже очищаем хранилища для безопасности
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('token');
        sessionStorage.clear();
        // Редирект
        window.location.href = '../html/authorization.html';
    });
}

// Перехватчик для добавления токена к запросам
function makeAuthenticatedRequest(url, options = {}) {
    options.credentials = 'include'; // Куки для аутентификации
    return fetch(url, options)
        .then(response => {
            if (response.status === 401) {
                // Попытка обновить токен при 401
                return refreshToken().then(() => {
                    // Повторить запрос (теперь с обновлёнными куками)
                    return fetch(url, options);
                });
            }
            return response;
        });
}

// Функция проверки авторизации (переиспользуемая)
export function checkAuth(redirectIfUnauthorized = true) {
    return fetch('http://127.0.0.1:8080/api/getUserId', {  
        method: 'GET',
        credentials: 'include'  // Куки автоматически
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('isLoggedIn');
                if (redirectIfUnauthorized) {
                    localStorage.setItem('redirectAfterLogin', window.location.href);
                    window.location.href = '../html/authorization.html';  // Или куда нужно
                }
                throw new Error('Unauthorized');
            }
            throw new Error('Server error');
        }
        return response.json();
    })
    .then(data => {
        console.log('Авторизован, userID:', data.userID);
        return data.userID;  // Возвращаем для использования
    })
    .catch(error => {
        console.error('Ошибка проверки авторизации:', error);
        if (redirectIfUnauthorized) {
            localStorage.removeItem('isLoggedIn');
            window.location.href = '../html/authorization.html';
        }
        throw error;
    });
}


