// auth.js
import * as auth from './authorizationFunctions.js';

document.getElementById('registerBtn').addEventListener('click', function() {
        const isAuthPage = /authorization\.html$/.test(window.location.pathname);
        if (!isAuthPage) sessionStorage.setItem('redirectAfterLogin', window.location.href);
        window.location.href = 'html/registration.html';
    });

  document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('loginBtn');
        loginBtn.addEventListener('click', (e) => {
            e.preventDefault();  // Предотвращает отправку формы
            auth.authorize();
        });
});
