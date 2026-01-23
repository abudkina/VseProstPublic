// forgot_password.js
// Обработка формы запроса восстановления пароля

const API_URL = window.location.origin + '/api';

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('forgotPasswordForm');
    const submitBtn = document.getElementById('submitBtn');
    const successMessage = document.getElementById('successMessage');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value.trim();
        
        if (!email) {
            alert('Введите email');
            return;
        }
        
        // Простая валидация email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('Введите корректный email');
            return;
        }
        
        // Блокируем кнопку
        submitBtn.disabled = true;
        submitBtn.textContent = 'Отправка...';
        
        try {
            const response = await fetch(`${API_URL}/forgot-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ email: email })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Скрываем форму и показываем сообщение об успехе
                form.style.display = 'none';
                document.querySelector('h1').style.display = 'none';
                document.querySelector('.description').style.display = 'none';
                successMessage.style.display = 'block';
            } else {
                alert(data.error || 'Произошла ошибка. Попробуйте позже.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Отправить ссылку';
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Ошибка соединения с сервером. Попробуйте позже.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Отправить ссылку';
        }
    });
});
