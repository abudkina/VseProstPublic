function logout() {
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

document.getElementById('logout').addEventListener('click', () => {
    logout();
    const redirectUrl = sessionStorage.getItem('redirectAfterLogin') || '../html/index.html';
    sessionStorage.removeItem('redirectAfterLogin');
    window.location.href = redirectUrl; // Редирект после логина
});