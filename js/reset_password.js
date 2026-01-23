// reset_password.js
// Обработка формы сброса пароля

const API_URL = window.location.origin + '/api';

// Получаем токен из URL
function getTokenFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('token');
}

// Показываем/скрываем элементы
function showElement(elementId) {
    document.getElementById(elementId).style.display = 'block';
}

function hideElement(elementId) {
    document.getElementById(elementId).style.display = 'none';
}

// Проверка токена при загрузке страницы
async function verifyToken(token) {
    try {
        const response = await fetch(`${API_URL}/verify-reset-token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ token: token })
        });
        
        const data = await response.json();
        
        hideElement('loadingMessage');
        
        if (response.ok && data.valid) {
            showElement('resetForm');
        } else {
            document.getElementById('errorText').textContent = 
                data.error || 'Ссылка для сброса пароля истекла или уже была использована.';
            showElement('errorMessage');
        }
    } catch (error) {
        console.error('Ошибка проверки токена:', error);
        hideElement('loadingMessage');
        document.getElementById('errorText').textContent = 
            'Ошибка соединения с сервером. Попробуйте позже.';
        showElement('errorMessage');
    }
}

// Сброс пароля
async function resetPassword(token, password, confirmPassword) {
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Сохранение...';
    
    try {
        const response = await fetch(`${API_URL}/reset-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                token: token,
                password: password,
                confirmPassword: confirmPassword
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            hideElement('resetForm');
            showElement('successMessage');
        } else {
            alert(data.error || 'Произошла ошибка. Попробуйте позже.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Сохранить новый пароль';
        }
    } catch (error) {
        console.error('Ошибка сброса пароля:', error);
        alert('Ошибка соединения с сервером. Попробуйте позже.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Сохранить новый пароль';
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const token = getTokenFromUrl();
    
    if (!token) {
        hideElement('loadingMessage');
        document.getElementById('errorText').textContent = 
            'Отсутствует токен для сброса пароля. Запросите новую ссылку.';
        showElement('errorMessage');
        return;
    }
    
    // Проверяем токен
    verifyToken(token);
    
    // Обработка формы
    const form = document.getElementById('resetPasswordForm');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        // Валидация
        if (password.length < 6) {
            alert('Пароль должен содержать минимум 6 символов');
            return;
        }
        
        if (password !== confirmPassword) {
            alert('Пароли не совпадают');
            return;
        }
        
        resetPassword(token, password, confirmPassword);
    });
    
    // Валидация в реальном времени
    const passwordField = document.getElementById('password');
    const confirmField = document.getElementById('confirmPassword');
    
    confirmField.addEventListener('input', function() {
        if (passwordField.value !== confirmField.value) {
            confirmField.setCustomValidity('Пароли не совпадают');
        } else {
            confirmField.setCustomValidity('');
        }
    });
    
    passwordField.addEventListener('input', function() {
        if (confirmField.value && passwordField.value !== confirmField.value) {
            confirmField.setCustomValidity('Пароли не совпадают');
        } else {
            confirmField.setCustomValidity('');
        }
    });
});
